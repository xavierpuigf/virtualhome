import random
import json
import re
import copy
import numpy as np
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
    
    body_part = ['face', 'leg', 'arm', 'eye', 'hand', 'feet']
    character_id = [i["id"] for i in filter(lambda v: v["class_name"] == 'character', graph_dict["nodes"])][0]

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

        # character is not sitting, lying, holding, not close to anything
        if node["class_name"] == 'character':
            # character is not inside anything 
            graph_dict["edges"] = [e for e in filter(lambda e: e["from_id"] != character_id and e["to_id"] != character_id, graph_dict["edges"])]

            # set the character inside the pre-specified room
            default_room_id = [i["id"] for i in filter(lambda v: v["class_name"] == 'living_room', graph_dict["nodes"])][0]
            graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": character_id, "to_id": default_room_id})

            node["states"] = []

        if "light" in node["class_name"]:
            node["states"].append("ON")

        if node["category"] == "Doors":
            node["states"].append("OPEN")

        if any([Property.BODY_PART in node["properties"] for v in body_part]):
            graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": character_id, "to_id": node["id"]})
            graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": node["id"], "to_id": character_id})
     

def add_missing_object_from_script(script, graph_dict, properties_data):

    possible_rooms = ['home_office', 'kitchen', 'living_room', 'bathroom', 'dining_room', 'bedroom', 'kids_bedroom', 'entrance_hall']
    available_rooms = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]
    available_rooms_id = [i['id'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]

    equivalent_rooms = {
        "kitchen": ["dining_room"], 
        "dining_room": ["kitchen"], 
        "entrance_hall": ["living_room"], 
        "home_office": ["living_room"], 
        "living_room": ["home_office"],
        "kids_bedroom": ["bedroom"]
    }
    room_mapping = {}
    for room in possible_rooms:
        if room not in available_rooms:
            assert room in equivalent_rooms, "Not pre-specified mapping for room: {}".format(room)
            room_mapping[room] = random.choice(equivalent_rooms[room])


    objects_in_script = {}
    room_name = None
    for script_line in script:
        for parameter in script_line.parameters:
            # room mapping
            if parameter.name in room_mapping:
                parameter.name = room_mapping[parameter.name]

            if parameter.name in available_rooms:
                room_name = parameter.name
                
            name = parameter.name
            if name in possible_rooms and name not in available_rooms:
                print("There is no {} in the environment".format(name))
                return None, False
            if (parameter.name, parameter.instance) not in objects_in_script:
                objects_in_script[(parameter.name, parameter.instance)] = parameter.instance


    available_nodes = copy.deepcopy(graph_dict['nodes'])
    available_name = list(set([node['class_name'] for node in available_nodes]))

    if room_name == None:
        # Room is not specified in this program, assign one to it
        hist = np.zeros(len(available_rooms_id))
        for obj in objects_in_script:
            obj_name = obj[0]
            for node in available_nodes:
                if node['class_name'] == obj_name:
                    edges = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] in available_rooms_id, graph_dict["edges"])]
                    
                    if len(edges) > 0:
                        for edge in edges:
                            dest_id = edge['to_id']
                            idx = available_rooms_id.index(dest_id)
                            hist[idx] += 1

        if hist.std() < 1e-5:
            # all equal
            room_name = random.choice(available_rooms)
            #print("Set a random_room")
        else:
            idx = np.argmax(hist)
            room_name = available_rooms[idx]
            #print("Pick room: {}".format(room_name))


    room_id = [i["id"] for i in filter(lambda v: v['class_name'] == room_name, graph_dict["nodes"])][0]
    id = 1000

    def _add_missing_node(_id, _obj, _category):
                
        graph_dict['nodes'].append({
            "properties": [i.name for i in properties_data[_obj[0]]], 
            "id": _id, 
            "states": [], 
            "category": _category, 
            "class_name": _obj[0]
        })
        objects_in_script[_obj] = _id
        return _id + 1

    for obj in objects_in_script.keys():
        if obj[0] in available_name:
            added = False
            # existing nodes
            for node in available_nodes:
                if node['class_name'] == obj[0]:
                    obj_in_room = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] == room_id, graph_dict["edges"])]
                    if obj[0] not in available_rooms and len(obj_in_room) == 0:
                        continue
                    else:
                        objects_in_script[obj] = node['id']
                        available_nodes.remove(node)
                        added = True
                        break
            if not added:
                # add edges
                graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": id, "to_id": room_id})
                id = _add_missing_node(id, obj, 'placing_objects')
        else:
            # add missing nodes
            graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": id, "to_id": room_id})
            id = _add_missing_node(id, obj, 'placing_objects')


    # change the id in script
    for script_line in script:
        for parameter in script_line.parameters:
            if parameter.name == 'kitchen':
                parameter.name = 'dining_room'

            parameter.instance = objects_in_script[(parameter.name, parameter.instance)]
            
    return objects_in_script, room_mapping


def prepare_from_precondition(precond, objects_in_script, room_mapping, graph_dict):

    relation_mapping = {
        "inside": "INSIDE", 
        "location": "INSIDE", 
        "atreach": "CLOSE", 
        "in": "ON"
    }
    for p in precond:
        for k, v in p.items():
            if k in ['location', 'inside', 'atreach', 'in']:
                src_name, src_id = v[0]
                tgt_name, tgt_id = v[1]
                src_id = int(src_id)
                tgt_id = int(tgt_id)
                # room mapping
                if tgt_name.lower() in room_mapping:
                    tgt_name = room_mapping[tgt_name.lower()]

                if k == 'location':
                    assert Room.has_value(tgt_name)

                src_id = objects_in_script[(src_name.lower().replace(' ', '_'), src_id)]
                tgt_id = objects_in_script[(tgt_name.lower().replace(' ', '_'), tgt_id)]

                graph_dict['edges'].append({'relation_type': relation_mapping[k], 'from_id': src_id, 'to_id': tgt_id})
                
            elif k in ['is_on', 'is_off', 'open']:
                obj_id = objects_in_script[(v[0].lower().replace(' ', '_'), int(v[1]))]
                for node in graph_dict['nodes']:
                    if node['id'] == obj_id:
                        if k == 'is_on':
                            if 'OFF' in node['states']: node['states'].remove('OFF')
                            node['states'].append('ON')
                        elif k == 'is_off':
                            if 'ON' in node['states']: node['states'].remove('ON')
                            node['states'].append('OFF')
                        elif k == 'open':
                            if 'CLOSED' in node['states']: node['states'].remove('CLOSED')
                            node['states'].append('OPEN')
                        break


def add_random_objs_graph_dict(object_placing, graph_dict, properties_data, n):

    relation_mapping = {
        "in": "INSIDE", 
        "on": "ON", 
        "nearby": "CLOSE"
    }

    objects_to_place = list(object_placing.keys())
    random.shuffle(objects_to_place)

    id = 2000
    while n > 0:

        src_name = random.choice(objects_to_place)
        tgt_names = copy.deepcopy(object_placing[src_name])
        random.shuffle(tgt_names)
        for tgt_name in tgt_names:

            tgt_nodes = [i for i in filter(lambda v: v["class_name"] == tgt_name['destination'], graph_dict["nodes"])]

            if len(tgt_nodes) > 0:
                tgt_node = tgt_nodes[0]
                tgt_id = tgt_node["id"]

                graph_dict['nodes'].append({
                    "properties": [i.name for i in properties_data[src_name]], 
                    "id": id, 
                    "states": [], 
                    "category": "placable_objects", 
                    "class_name": src_name
                })

                graph_dict["edges"].append({'relation_type': relation_mapping[tgt_name["relation"].lower()], "from_id": id, "to_id": tgt_id})
                id += 1
                n -= 1
                break


def random_change_object_state(objects_in_script, object_states, graph_dict, object_placing, properties_data):

    states_mapping = {
        "dirty": "dirty", 
        "clean": "clean", 
        "open": "open", 
        "closed": "closed", 
        "plugged": "plugged_in", 
        "unplugged": "plugged_out", 
        "on": "on", 
        "off": "off"
    }

    def _sample_states(possible_states):
        state = random.choice(possible_states)
        return state

    object_id_in_program = [i for i in objects_in_script.values()]
    available_states = ['dirty', 'clean', 'open', 'closed', 'free', 'occupied', 'plugged', 'unplugged', 'on', 'off']
    for node in graph_dict["nodes"]:
        if node["id"] in object_id_in_program:
            continue

        if node["class_name"] in object_states:
            possible_states = object_states[node["class_name"]]
            possible_states = [i for i in filter(lambda v: v in available_states, possible_states)]
            if len(possible_states) == 0:
                continue

            state = _sample_states(possible_states)
            if state in ['free', 'occupied']:
                if 'SITTABLE' in node['properties']:
                    node_id = node['id']
                    continue
            else:
                state = states_mapping[state]
                if state not in node["states"]:
                    if state == 'dirty':
                        if 'clean' in node["states"]:
                            node["states"].remove('clean')
                        node["states"].append(state)
                    if state == 'clean':
                        if 'dirty' in node["states"]:
                            node["states"].remove('dirty')
                        node["states"].append(state)

                    if state == 'on':
                        if 'off' in node["states"]:
                            node["states"].remove('off')
                        node["states"].append(state)
                    if state == 'off':
                        if 'on' in node["states"]:
                            node["states"].remove('on')
                        node["states"].append(state)

                    if state == 'open':
                        if 'closed' in node["states"]:
                            node["states"].remove('closed')
                        node["states"].append(state)
                    if state == 'closed':
                        if 'open' in node["states"]:
                            node["states"].remove('open')
                        node["states"].append(state)

                    if state == 'plugged_in':
                        if 'plugged_out' in node["states"]:
                            node["states"].remove('plugged_out')
                        node["states"].append(state)
                    if state == 'plugged_out':
                        if 'plugged_in' in node["states"]:
                            node["states"].remove('plugged_in')
                        node["states"].append(state)

