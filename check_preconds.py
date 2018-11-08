# Check if a set of graphs follow the preconds
import os
from tqdm import tqdm
import re
import glob
import json
import ipdb
total_cont = 0
progs_error = []
state_node = ['is_on', 'is_off', 'plugged', 'unplugged', 'open', 'closed', 'clean', 'dirty', 'sitting', 'lying']
state_edge = ['inside', 'location', 'atreach', 'in']
equivalent_rooms = {
        "kitchen": ["dining_room"], 
        "dining_room": ["kitchen"], 
        "entrance_hall": ["living_room"], 
        "home_office": ["living_room"], 
        "living_room": ["home_office", "entrance_hall"],
        "kids_bedroom": ["bedroom"],
        "bedroom": ["kids_bedroom", "bedroom"]
    }

map_state = {
        "dirty": "DIRTY", 
        "clean": "CLEAN", 
        "open": "OPEN", 
        "closed": "CLOSED", 
        "plugged": "PLUGGED_IN", 
        "unplugged": "PLUGGED_OUT", 
        "is_on": "ON", 
        "is_off": "OFF", 
        "sitting": "SITTING", 
        "lying": "LYING"
}
map_edge = {
        "inside": "INSIDE", 
        "location": "INSIDE", 
        "atreach": "CLOSE", 
        "in": "ON"
}
def check_preconds(graph_path, precon_path, mapping_path, errors):
    print(len(progs_error))
    try:
        with open(mapping_path, 'r') as f:
            instructions = f.readlines()
        with open(precon_path, 'r') as f:
            json_precond = json.load(f)
        with open(graph_path, 'r') as f:
            json_graph = json.load(f)
    except:
        exists = [os.path.isfile(nf) for nf in [graph_path, precon_path, mapping_path]]
        print('A file does not exist', exists)
        return errors
    if len(json_precond) == 0:
        return errors
    
    try:
        mapping = parse_mapping(instructions)
    except:
        if 'idscript_mismatch' not in errors:
            errors['idscript_mismatch'] = 0
        errors['idscript_mismatch'] += 1
        return errors

    init_state = json_graph['graph_state_list'][0]
    subgraph = precond_to_id(json_precond, mapping)
    for node in subgraph['nodes']:
        continue
        #print(node)
        
    for edge in subgraph['edges']:
        id1, rel, id2 = edge
        if id1 == id2:
            continue
        # Check if element is not present
        edges_original = [edge_or for edge_or in init_state['edges'] 
                          if edge_or['relation_type'] == rel and edge_or['from_id'] == int(id1) and edge_or['to_id'] == int(id2)]
        edges_instead = [edge_or for edge_or in init_state['edges'] 
                          if edge_or['relation_type'] == rel and edge_or['from_id'] == int(id1)]
        if len(edges_original) == 0:
            if rel != 'INSIDE':
                ipdb.set_trace()
            print(graph_path)
            progs_error.append(graph_path)
            return errors
    return errors

def precond_to_id(json_precond, mapping):
    sub_graph = {'nodes': [], 'edges': []}
    for precon in json_precond:
        relation_name = list(precon.keys())[0]
        if relation_name in state_node:
            if precon[relation_name][0] == 'character':
                continue
            node_id = mapping[tuple(precon[relation_name])]
            translated_precond = map_state[relation_name]
            sub_graph['nodes'].append((node_id, translated_precond))
        elif relation_name in state_edge:
            if precon[relation_name][0][0] == 'character':
                continue
            if precon[relation_name][1][0] == 'character':
                continue
            node_id1 = mapping[tuple(precon[relation_name][0])]
            node_id2 = mapping[tuple(precon[relation_name][1])]
            trans_rel = map_edge[relation_name]
            sub_graph['edges'].append((node_id1, trans_rel, node_id2))
        else:
            pass
    return sub_graph

def parse_mapping(instructions):
    instructions = instructions[4:]
    dict_mapping = {}
    for instruction in instructions:
        arguments = re.findall('\<.*\> \(.*\)', instruction.strip())
        for argument in arguments:
            argname = argument.split('>')[0][1:]
            argid = argument.split('(')[1][:-1]

            argnames = [argname]
            if argname in list(equivalent_rooms.keys()):
                argnames += equivalent_rooms[argname]
            for arg in argnames:    
                tuplen = (arg, argid.split('.')[0])
                idn = argid.split('.')[1]
                if tuplen in dict_mapping.keys() and dict_mapping[tuplen] != idn:
                    raise Exception
                dict_mapping[tuplen] = idn
    return dict_mapping

def obtain_graph_and_preconds(path):
    # path is a path to state_list
    parts = path.split('/state_list/')
    first_part = parts[0]
    second_part = '/'.join(parts[1].split('/')[1:])
    mapping_path = path.replace('state_list', 'executable_programs').replace('.json', '.txt')
    precond_path = '{}/initstate/{}'.format(first_part, second_part)
    return path,precond_path, mapping_path

files = glob.glob('programs_all_graphs/programs_processed_precond_nograb_morepreconds/state_list/*/*/*.json')
errors = {}
for i in tqdm(range(len(files))):
    graph_path, precond_path, mapping_path = obtain_graph_and_preconds(files[i])
    check_preconds(graph_path, precond_path, mapping_path, errors)
print(len(set(progs_error)))
