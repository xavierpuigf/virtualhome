import json
import re
from environment import EnvironmentGraph, Property
import ipdb


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)


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

def create_graph_from_precond(script, precond, properties_data):
    
    patt_params = r'<([\w\s]+)>\s*\((\d+)\)'

    relation_mapping = {
        "inside": "INSIDE", 
    }
    state_mapping = {
        "is_off": "OFF", 
        "closed": "CLOSED"
    }

    def _add_edges(data):
        for p in precond:
            if "-->" in p:
                relation, params = p.split(': ')
                relation = relation_mapping[relation]

                param_match = re.search(patt_params, params)
                src_id = int(param_match.group(2))
                param_match = re.search(patt_params, param_match.string[param_match.end(2):])
                tgt_id = int(param_match.group(2))
                data['edges'].append({"relation_type": relation, "from_id": src_id, "to_id": tgt_id})

    def _add_states(data):
        for p in precond:
            if "-->" not in p:
                state, params = p.split(': ')
                state = state_mapping[state]

                param_match = re.search(patt_params, params)
                id = int(param_match.group(2))
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
        if class_name == 'basket for clothes':
            class_name = 'basket of clothes'
        node = {
            "properties": properties_data[class_name.replace(' ', '')],
            "id": id, 
            "states": [], 
            "class_name": class_name
        }
        data["nodes"].append(node)

    _add_edges(data)
    _add_states(data)

    return EnvironmentGraph(data)