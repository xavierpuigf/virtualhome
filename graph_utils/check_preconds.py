# Check if a set of graphs follow the preconds
import os
from tqdm import tqdm
import re
import glob
import json
import ipdb
from utils import *
total_cont = 0
progs_error = []
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
            progs_error.append(graph_path)
            return errors
    return errors



def obtain_graph_and_preconds(path):
    # path is a path to state_list
    parts = path.split('/state_list/')
    first_part = parts[0]
    second_part = '/'.join(parts[1].split('/')[1:])
    mapping_path = path.replace('state_list', 'executable_programs').replace('.json', '.txt')
    precond_path = '{}/initstate/{}'.format(first_part, second_part)
    return path,precond_path, mapping_path

files = glob.glob('programs_all_graphs2/programs_processed_precond_nograb_morepreconds/state_list/*/*/*.json')
errors = {}
for i in tqdm(range(len(files))):
    graph_path, precond_path, mapping_path = obtain_graph_and_preconds(files[i])
    check_preconds(graph_path, precond_path, mapping_path, errors)
print(len(set(progs_error)))
