import random
import json
import re
from environment import EnvironmentGraph, Property, Room
import ipdb

random.seed(123)


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)

def load_graph_dict(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data

def load_name_equivalence(file_name='resources/class_name_equivalence.json'):
    with open(file_name) as f:
        return json.load(f)


def load_object_placing(file_name='resources/object_placing.json'):
    with open(file_name) as f:
        return json.load(f)


def load_properties_data(file_name='resources/properties_data.json'):
    with open(file_name) as f:
        pd_dict = json.load(f)
        return {key: [Property[p] for p in props] for (key, props) in pd_dict.items()}


def set_to_default_state(graph_dict):
    

    for node in graph_dict["nodes"]:

        # always set to off, closed, open
        if "CAN_OPEN" in node["properties"]:
            if "OPEN" in node["states"]:
                node["states"].remove("OPEN")
            node["states"].append("CLOSED")
        if "HAS_PLUG" in node["properties"]:
            if "PLUGGED_OUT" in node["states"]:
                node["states"].remove("PLUGGED_OUT")
            node["states"].append("PLUGGED_IN")
        if "HAS_SWTICH" in node["properties"]:
            if "ON" in node["states"]:
                node["states"].remove("ON")
            node["states"].append("OFF")

        # everyhting is clean
        if "DIRTY" in node["states"]:
            node["states"].remove("DIRTY")

        # character is not sitting, lying
        if node["class_name"] == 'character':
            node["states"] = []

        if "light" in node["class_name"]:
            node["states"].append("ON")

        if node["category"] == "Doors":
            node["states"].append("OPEN")


def create_graph_dict_from_precond(script, precond, properties_data):
    
    patt_params = r'<([\w\s]+)>\s*\((\d+)\)'

    relation_mapping = {
        "inside": "INSIDE", 
        "location": "INSIDE", 
        "atreach": "CLOSE", 
        "in": "ON"
    }
    state_mapping = {
        "is_off": "OFF", 
        "is_on": "ON", 
        "open": "OPEN"
    }

    def _add_edges(data):
        for p in precond:
            for k, v in p.items():
                if k in ['location', 'atreach', 'inside', 'in']:
                    relation = k
                    relation = relation_mapping[relation]

                    src_id = v[0][1]
                    tgt_id = v[1][1]
                    data['edges'].append({"relation_type": relation, "from_id": src_id, "to_id": tgt_id})

    def _add_states(data):
        for p in precond:
            for k, v in p.items():
                if k in ['is_on', 'is_off', 'open']:
                    state = k
                    state = state_mapping[state]
                    id = v[1]
                    for n in data["nodes"]:
                        if n["id"] == id:
                            n["states"].append(state)


    character_node = {
        "properties": [], 
        "id": 0, 
        "states": [], 
        "class_name": "character"
    }
    data = {
        "edges": [], 
        "nodes": [character_node]
    }

    all_instances = []
    for script_lines in script._script_lines:
        for parameter in script_lines.parameters:
            all_instances.append((parameter.name, parameter.instance))

    all_instances = list(set(all_instances))


    for instance in all_instances:
        class_name, id = instance

        if Room.has_value(class_name.replace(' ', '_')):
            node = {
                "properties": [],
                "id": id, 
                "states": [], 
                "class_name": class_name, 
                "category": 'Rooms'
            }
        else:
            node = {
                "properties": properties_data[class_name.replace(' ', '')],
                "id": id, 
                "states": [], 
                "class_name": class_name
            }

        data["nodes"].append(node)

    _add_edges(data)
    _add_states(data)

    return data


def perturb_graph_dict(graph_dict, object_placing, properties_data, n):

    objects = list(object_placing.keys())
    random.shuffle(objects)

    selected_objects = objects[:n]
    id = len(graph_dict["nodes"])
    new_added_container = {}
    all_room_nodes = list(filter(lambda v: "category" in v and v["category"] == 'Rooms', [node for node in graph_dict["nodes"]]))

    for obj in selected_objects:

        nodes = []
        edges = []

        placing_info = random.choice(object_placing[obj])
        relation = placing_info['relation']
        room = placing_info['room']
        destination = placing_info['destination']

        if obj.replace(' ', '') not in properties_data.keys() or destination.replace(' ', '') not in properties_data.keys():
            continue

        src_node = {
            "properties": properties_data[obj.replace(' ', '')], 
            "id": id, 
            "states": [], 
            "class_name": obj
        }
        nodes.append(src_node)
        src_id = id
        id += 1

        if destination not in new_added_container.keys():
            tgt_node = {
                "properties": properties_data[destination.replace(' ', '')], 
                "id": id, 
                "states": [], 
                "class_name": destination
            }
            nodes.append(tgt_node)
            new_added_container.update({destination: id})
            tgt_id = id
            id += 1
        else:
            tgt_id = new_added_container[destination]

        if not room is None:
            pass

        edges.append({
            "relation_type": relation.upper(), 
            "from_id": src_id, 
            "to_id": tgt_id
        })

        graph_dict["nodes"].extend(nodes)
        graph_dict["edges"].extend(edges)
        