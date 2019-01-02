# Augments the dataset by removing preconds and correcting
import glob
import random
import numpy as np
import shutil
import os
import json
import exception_handler
import ipdb
import re
from collections import Counter
from multiprocessing import Process, Manager, current_process
from tqdm import tqdm
import sys
from termcolor import colored


import augmentation_utils

sys.path.append('..')
import check_programs
import utils

random.seed(123)
np.random.seed(123)

# Options
verbose = False
thres = 300
write_augment_data = True
multi_process = True
num_processes = os.cpu_count()

# Paths
augmented_data_dir = 'augment_exception'

if write_augment_data:
    if not os.path.exists(augmented_data_dir):
        os.makedirs(augmented_data_dir)

all_programs_exec = glob.glob('original_programs/executable_programs/*/*/*.txt')
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


prog_folder = 'original_programs'
programs = [('{}/withoutconds/{}'.format(prog_folder, prog_name), apt) for prog_name, apt in programs_to_apt.items()]


objects_occupied = [
    'couch',
    'bed',
    'chair',
    'loveseat',
    'sofa',
    'toilet',
    'pianobench',
    'bench']


def to_hash(precond_list):
    pr_list = precond_list.copy()
    for it, elem in enumerate(pr_list):
        # dictionary of lists
        key_elem = list(elem)[0]
        values = elem[key_elem]
        for v_id, v in enumerate(values):
            if isinstance(v, list):
                values[v_id] = tuple(v)
        values = tuple(values)
        tuple_dict = (key_elem, values)
        pr_list[it] = tuple_dict
    return tuple(sorted(pr_list))


def from_hash(precond_tuple):
    precond_list = list(precond_tuple)
    for it, elem in enumerate(precond_list):
        key_elem = elem[0]
        values = [x for x in elem[1]]
        for v_id, v in enumerate(values):
            if isinstance(v, tuple):
                values[v_id] = list(v)
        precond_list[it] = {key_elem: values}
    return precond_list


def augment_dataset(d, programs):
    programs = np.random.permutation(programs).tolist()
    exceptions_not_found = []
    for program_name, apt_name in tqdm(programs):
        augmented_progs_i = []
        augmented_progs_i_new_inst = []
        augmented_preconds_i = []
        init_graph_i = []
        end_graph_i = []
        state_list_i = []
        augmented_precond_candidates = []
        if program_name in d.keys(): 
            continue
        if multi_process:
            d[program_name] = str(current_process())
        if len(d.keys()) % 20 == 0 and verbose:
            print(len(d.keys()))

        state_file = program_name.replace(
                'withoutconds', 'initstate').replace('.txt', '.json')

        with open(program_name, 'r') as f:
            lines_program = f.readlines()
            program = lines_program[4:]
        
        with open(state_file, 'r') as f:
            init_state = json.load(f)

        hprev_state = to_hash(init_state.copy())
        
        # Obtain all the objects in a program
        objects_program = []
        for instr in program:
            _, objects, indx = augmentation_utils.parseStrBlock(instr.strip())
            for ob, idi in zip(objects, indx):
                objects_program.append([ob, idi])
        
        prob_modif = 0.7
        for _ in range(thres):
            modified_state = init_state.copy()
            # Remove sitting
            modified_state = [x for x in modified_state if list(x)[0] != 'sitting' or random.random() > prob_modif] 
            # Remove at reach
            modified_state = [x for x in modified_state if list(x)[0] != 'atreach' or random.random() > prob_modif]
            # Swap plugged
            modified_state = [x if list(x)[0] != 'plugged' or random.random() > prob_modif else {'unplugged': x[list(x)[0]]} for x in modified_state]
            # Swap unplugged
            modified_state = [x if list(x)[0] != 'unplugged' or random.random() > prob_modif else {'plugged': x[list(x)[0]]} for x in modified_state ]
            # Swap is_on
            modified_state = [x if list(x)[0] != 'is_on' or random.random() > prob_modif else {'is_off': x[list(x)[0]]} for x in modified_state]
            # Swap is_off
            modified_state = [x if list(x)[0] != 'is_off' or random.random() > prob_modif else {'is_on': x[list(x)[0]]} for x in modified_state]
            # Swap open
            modified_state = [x  if list(x)[0] != 'open' or random.random() > prob_modif else {'closed': x[list(x)[0]]} for x in modified_state]
            # Swap is_closed
            modified_state = [x if list(x)[0] != 'closed' or random.random() > prob_modif else {'open': x[list(x)[0]]} for x in modified_state ]
            # Swap is free
            modified_state = [x if list(x)[0] != 'free' or random.random() > prob_modif else {'occupied': x[list(x)[0]]} for x in modified_state ]
            

            # convert to hashable type
            hmodified_state = to_hash(modified_state)
            if hmodified_state != hprev_state:
                augmented_precond_candidates.append(hmodified_state)

        augmented_precond_candidates = list(set(augmented_precond_candidates))
        lines_program_orig = lines_program.copy()
        
        # back to dict
        augmented_precond_candidates = [from_hash(hp) for hp in augmented_precond_candidates]
        if verbose:
            print('Augmented precond candidates: {}'.format(len(augmented_precond_candidates)))
        
        maximum_iters = 20
        for j, init_state in enumerate(augmented_precond_candidates):
            lines_program = lines_program_orig.copy()
            executable = False
            max_iter = 0
            input_graph = None
            id_mapping = {}
            info = {}
            message_acum = []
            program_acum = []
            while not executable and max_iter < maximum_iters and lines_program is not None:        
                (message, final_state, graph_state_list, input_graph, 
                id_mapping, info, graph_helper) = check_programs.check_script(
                        lines_program, 
                        init_state, 
                        '../example_graphs/{}.json'.format(apt_name),
                        input_graph,
                        id_mapping,
                        info)
                message_acum.append(message)
                program_acum.append(lines_program)
                if False:
                    print('Error reading', lines_program)
                    lines_program = None
                    continue
                if message is None:
                    lines_program = None
                    continue
                lines_program = [x.strip() for x in lines_program]
                if 'is executable' not in message:
                    lines_program = exception_handler.correctedProgram(
                            lines_program, init_state, final_state, message, verbose, id_mapping)
                    max_iter += 1
                else:
                    executable = True

                if isinstance(lines_program, tuple) and lines_program[0] is None:
                    lines_program = None
                    continue


            # Save the program
            if executable and max_iter > 0:
                lines_program_newinst = lines_program[:4]
                for lp in lines_program[4:]:
                    action, objects, indx = augmentation_utils.parseStrBlock(lp.strip())
                    instruction = '[{}]'.format(action)
                    for obj, idis in zip(objects, indx):
                        idi = int(idis)
                        obj_name = obj
                        if (obj_name in graph_helper.possible_rooms and 
                            (obj_name, idi) not in id_mapping):
                            obj_name = graph_helper.equivalent_rooms[obj_name]
                        try:
                            graphid = id_mapping[(obj_name, idi)]
                        except:
                            print(program_name, lp)
                        instruction += ' <{}> ({}.{})'.format(obj_name, idi, graphid)
                    lines_program_newinst.append(instruction)
                
                augmented_progs_i_new_inst.append(lines_program_newinst)
                augmented_preconds_i.append(init_state)
                augmented_progs_i.append(lines_program)
                init_graph_i.append(input_graph)
                end_graph_i.append(final_state)
                state_list_i.append(graph_state_list)
            
            elif not executable:
                print(max_iter, program_name)
                if verbose:
                    print(colored('Program not solved, {} iterations tried'.format(max_iter), 'red'))
                    print('\n'.join(message_acum))
                    # if lines_program:
                    #     print(''.join(lines_program_orig))
                    #     print('---')
                    #     print('\n'.join(lines_program))

        if write_augment_data:
            augmentation_utils.write_data(augmented_data_dir, program_name, augmented_progs_i)
            augmentation_utils.write_data(augmented_data_dir, program_name, augmented_progs_i_new_inst, 
                    'executable_programs/{}/'.format(apt_name))
            augmentation_utils.write_precond(augmented_data_dir, program_name, augmented_preconds_i)
            augmentation_utils.write_graph(augmented_data_dir, program_name, init_graph_i, end_graph_i, state_list_i,
                    apt_name)
        #print('\n'.join(exceptions_not_found))

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
