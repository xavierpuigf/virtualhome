from utils import *
import re
import json
import os
import glob
from tqdm import tqdm
# Commands to modify the graphs

def obtain_graph_and_preconds(path):
    # path is a path to state_list
    parts = path.split('/state_list/')
    first_part = parts[0]
    second_part = '/'.join(parts[1].split('/')[1:])
    mapping_path = path.replace('state_list', 'executable_programs').replace('.json', '.txt')
    precond_path = '{}/initstate/{}'.format(first_part, second_part)
    return path,precond_path, mapping_path

def switchLights(graph_path, precond_path, mapping_path, errors):
    try:
        with open(mapping_path, 'r') as f:
            instructions = f.readlines()
        with open(precond_path, 'r') as f:
            json_precond = json.load(f)
        with open(graph_path, 'r') as f:
            json_graph = json.load(f)
    except:
        exists = [os.path.isfile(nf) for nf in [graph_path, precond_path, mapping_path]]
        print('A file does not exist', exists)
        return
    mapping = parse_mapping(instructions)
    init_state = json_graph['graph_state_list'][0]
    # Check all the lights that are off or on 
    preconds = [x for x in json_precond if list(x)[0] in ['is_off', 'is_on']]
    nodes_with_preconds = []
    for prec in preconds:
        objectn, idn = list(prec.values())[0]
        nodes_with_preconds.append(int(mapping[(objectn, idn)]))

    # Get all nodes that dont appear and are off
    for iti in range(len(json_graph['graph_state_list'])):
        nodes_graph_id = [il for il, node in enumerate(json_graph['graph_state_list'][iti]['nodes']) 
                if (('light' in node['class_name'] or 'lamp' in node['class_name']) and  
                    node['id'] not in nodes_with_preconds and 'ON' not in node['states'])]
        for il in nodes_graph_id:
            new_states = [st for st in json_graph['graph_state_list'][iti]['nodes'][il]['states'] if st != 'OFF'] + ['ON']
            json_graph['graph_state_list'][iti]['nodes'][il]['states'] = new_states
    with open(graph_path, 'w+') as f:
        json.dump(json_graph, f)
    with open(graph_path.replace('state_list', 'init_and_final_graphs'), 'w+') as f:
        json.dump([json_graph['graph_state_list'][0], json_graph['graph_state_list'][-1]], f)

files = glob.glob('../programs_all_graphs2/programs_processed_precond_nograb_morepreconds/state_list/*/*/*.json')
#  augmented_location_multiapts_allgraphs/

from random import shuffle
shuffle(files)
for i in tqdm(range(len(files))):
    nicename = files[i].replace('/', '_').replace('.', '_')
    if os.path.isfile('logs2/{}.log'.format(nicename)):
        print('exists')
        continue
    with open('logs2/{}.log'.format(nicename), 'w+') as f:
        f.write('started')
    graph_path, precond_path, mapping_path = obtain_graph_and_preconds(files[i])
    switchLights(graph_path, precond_path, mapping_path, {})
    with open('logs2/{}.log'.format(nicename), 'w+') as f:
        f.write('done')
if not os.path.isfile('logs/done.log'):
    with open('logs2/done.log', 'w+') as f:
        f.write('ok')

