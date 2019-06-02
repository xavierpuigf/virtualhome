# Augments the dataset by replacing object containers with other containers 
# where these objects tipically go
import os
import sys
import glob
import random
import pdb
import copy
import json
import numpy as np
import ast


from multiprocessing import Process, Manager, current_process
from tqdm import tqdm
from scipy.io import *

import augmentation_utils

import sys
sys.path.append('../simulation/')
import evolving_graph.check_programs as check_programs
import evolving_graph.utils as utils


random.seed(123)
np.random.seed(123)


# Options
verbose = True
thres = 300
write_augment_data = True
multi_process = False
num_processes = os.cpu_count() // 2


# Paths
path_object_placing = '../resources/object_script_placing.json'
augmented_data_dir = '../dataset/augment_location'
original_program_folder = '../dataset/programs_processed_precond_nograb_morepreconds/'

if write_augment_data:
    if not os.path.exists(augmented_data_dir):
        os.makedirs(augmented_data_dir)

all_programs_exec = glob.glob('{}/executable_programs/*/*/*.txt'.format(original_program_folder))
all_programs_exec = [x.split('executable_programs/')[1] for x in all_programs_exec]


# Obtain a mapping from program to apartment
programs_to_apt = {}
for program in all_programs_exec:
    program_name = '/'.join(program.split('/')[1:])
    apt_name = program.split('/')[0]
    if program_name not in programs_to_apt:
        programs_to_apt[program_name] = []
    programs_to_apt[program_name].append(apt_name)


# Pick a single scene by program
programs_to_apt_single = {}
for prog, apt_names in programs_to_apt.items():
    index = np.random.randint(len(apt_names))
    apt_single = apt_names[index]
    programs_to_apt[prog] = apt_single

programs = [('{}/withoutconds/{}'.format(original_program_folder, prog_name), apt) for prog_name, apt in programs_to_apt.items()]


# maps every object, and location to all the possible objects
with open(path_object_placing, 'r') as f:
    info_locations = json.loads(f.read())
merge_dict = {}
all_conts = 0
for obj_name in info_locations.keys():
    children = info_locations[obj_name]
    for it, child in enumerate(children):
        other_object = child['destination']
        relation = child['relation']
        if (obj_name, relation) not in merge_dict.keys():
            merge_dict[(obj_name, relation)] = []
        merge_dict[(obj_name, relation)].append(other_object)

precondtorelation = {
    'in': 'ON',
    'inside': 'IN'
}

 
def augment_dataset(d, programs):
    programs = np.random.permutation(programs).tolist()
    for program_name, apt_name in tqdm(programs):

        augmented_progs_i = []
        augmented_progs_i_new_inst = []
        augmented_preconds_i = []
        state_list_i = []
        if program_name in d.keys(): 
            continue
        if multi_process:
            d[program_name] = str(current_process())
        if len(d.keys()) % 20 == 0 and verbose:
            print(len(d.keys()))

        state_file = program_name.replace('withoutconds', 'initstate').replace('.txt', '.json')

        with open(program_name, 'r') as f:
            lines_program = f.readlines()
            program = lines_program[4:]

        with open(state_file, 'r') as fst:
            init_state = json.load(fst)
       
        # for every object, we list the objects that are inside, on etc.
        # they will need to be replaced by containers having the same
        # objects inside and on
        relations_per_object = {}
        for cstate in init_state:
            precond = [k for k in cstate.keys()][0]
            if precond in precondtorelation.keys():
                relation = precondtorelation[precond]
                object1 = cstate[precond][0][0]
                container = tuple(cstate[precond][1])
                if container not in relations_per_object.keys():
                    relations_per_object[container] = []
                relations_per_object[container] += [(object1, relation)]

        # Given all the containers, check which objects can go there
        object_replace_map = {}
        for container in relations_per_object.keys():
            replace_candidates = [] 
            for object_and_relation in relations_per_object[container]:
                if object_and_relation in merge_dict.keys():
                    replace_candidates.append(merge_dict[object_and_relation])

            # do a intersection of all the replace candidates
            intersection = []
            object_replace_map[container] = []
            # if there are objects we can replace
            if len(replace_candidates) > 0  and len([l for l in replace_candidates if len(l) == 0]) == 0: 
                intersection = list(set.intersection(*[set(l) for l in replace_candidates]))
                candidates = [x for x in intersection if x != container[0]]
                if len(candidates) > 0:
                    # How many containers to replace
                    cont = random.randint(1, min(len(candidates), 5)) 
                    # sample candidates
                    if cont > 1:
                        object_replace = random.sample(candidates, cont-1)
                        object_replace_map[container] += object_replace

        objects_prog = object_replace_map.keys()
        npgs = 0
        # Cont has, for each unique object, the number of objects we will replace it with
        cont = []
        for obj_and_id in objects_prog:
            cont.append(len(object_replace_map[obj_and_id]))

        # We obtain all the permutations given cont
        ori_precond = init_state
        recursive_selection = augmentation_utils.recursiveSelection(cont, 0, [])

        # For every permutation, we compute the new program
        for rec_id in recursive_selection:
            # change program
            new_lines = program
            precond_modif = copy.deepcopy(ori_precond)
            precond_modif = str(precond_modif).replace('\'', '\"')

            for iti, obj_and_id in enumerate(objects_prog):
                orign_object, idi = obj_and_id
                object_new = object_replace_map[obj_and_id][rec_id[iti]]
                new_lines = [x.replace('<{}> ({})'.format(orign_object, idi), 
                                   '<{}> ({})'.format(object_new.lower().replace(' ', '_'), idi)) for x in new_lines]
                precond_modif = precond_modif.replace('[\"{}\", \"{}\"]'.format(orign_object, idi), '[\"{}\", \"{}\"]'.format(object_new.lower().replace(' ', '_'), idi))


            
            try:
                init_state = ast.literal_eval(precond_modif)
                (message, final_state, graph_state_list, input_graph, 
                    id_mapping, info, graph_helper, modified_script) = check_programs.check_script(
                            new_lines, 
                            init_state, 
                            '../example_graphs/{}.json'.format(apt_name),
                            None,
                            False,
                            {},
                            {})
            except:
                pdb.set_trace()

            # Convert the program
            lines_program_newinst = []
            for script_line in modified_script:
                script_line_str = '[{}]'.format(script_line.action.name)
                if script_line.object():
                    script_line_str += ' <{}> ({})'.format(script_line.object().name, script_line.object().instance)
                if script_line.subject():
                    script_line_str += ' <{}> ({})'.format(script_line.subject().name, script_line.subject().instance)

                for k, v in id_mapping.items():
                    obj_name, obj_number = k
                    id = v
                    script_line_str = script_line_str.replace('<{}> ({})'.format(obj_name, id), 
                                                              '<{}> ({}.{})'.format(obj_name, obj_number, id))
                lines_program_newinst.append(script_line_str)

            augmented_progs_i_new_inst.append(lines_program_newinst)
            state_list_i.append(graph_state_list)
            augmented_progs_i.append(new_lines)         
            augmented_preconds_i.append(init_state)
            npgs += 1
            if npgs > thres:
                break

        # The current program
        if write_augment_data:
            augmentation_utils.write_data(augmented_data_dir, program_name, augmented_progs_i)
            augmentation_utils.write_data(augmented_data_dir, program_name, augmented_progs_i_new_inst, 
                                          'executable_programs/{}/'.format(apt_name))
            augmentation_utils.write_precond(augmented_data_dir, program_name, augmented_preconds_i)
            augmentation_utils.write_graph(augmented_data_dir, program_name, state_list_i, apt_name)


processes = []
if multi_process:
    manager = Manager()
    programs_done = manager.dict()
    for m in range(num_processes):
        
        p = Process(target=augment_dataset, args=(programs_done, programs))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

else:
    augment_dataset({}, programs)

