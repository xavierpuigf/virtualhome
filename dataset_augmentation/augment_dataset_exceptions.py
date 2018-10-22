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
import sys
from termcolor import colored

sys.path.append('..')
import check_programs

verbose = False
thres = 300
write_augment_data = True

if write_augment_data:
    augmented_data_dir = 'augmented_program_exception2'
    if not os.path.exists(augmented_data_dir):
        os.makedirs(augmented_data_dir)

prog_folder = 'programs_processed_precond_nograb_morepreconds'
programs = glob.glob('{}/withoutconds/*/*.txt'.format(prog_folder))


cont = 0

def write_data(ori_path, all_new_progs):
    
    # make_dirs
    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, 'withoutconds', sub_dir, old_name)
    assert not os.path.exists(new_dir), ipdb.set_trace()
    os.makedirs(new_dir)

    for j, new_progs in enumerate(all_new_progs):
        new_f = open('{}/{}.txt'.format(new_dir, j), 'w')
        nnew_progs = [x+'\n' for x in new_progs]
        for lines in nnew_progs:
            new_f.write(lines)
        new_f.close()    


def write_precond(ori_path, all_new_preconds):
    
    # make_dirs
    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, 'initstate', sub_dir, old_name)
    assert not os.path.exists(new_dir), ipdb.set_trace()
    os.makedirs(new_dir)

    for j, new_precond in enumerate(all_new_preconds):
        new_f = open('{}/{}.json'.format(new_dir, j), 'w')
        new_f.write(new_precond)
        new_f.close()   

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
    for program in programs:
        augmented_progs_i = []
        augmented_preconds_i = []
        augmented_precond_candidates = []
        if program in d.keys(): 
            continue
        d[program] = str(current_process())
        if len(d.keys()) % 20 == 0:
            print(len(d.keys()))
        state_file = program.replace(
                'withoutconds', 'initstate').replace('.txt', '.json')

        with open(program, 'r') as f:
            lines_program = f.readlines()
            
        with open(state_file, 'r') as f:
            init_state = json.load(f)

        hprev_state = to_hash(init_state.copy())
        modified_state = init_state

        
        prob_modif = 0.6
        for _ in range(thres):
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
            # Swap is_off
            modified_state = [x if list(x)[0] != 'closed' or random.random() > prob_modif else {'open': x[list(x)[0]]} for x in modified_state ]
            
            # convert to hashable type
            hmodified_state = to_hash(modified_state)
            if hmodified_state != hprev_state:
                augmented_precond_candidates.append(hmodified_state)

        augmented_precond_candidates = list(set(augmented_precond_candidates))
        lines_program_orig = lines_program.copy()
        
        # back to dict
        augmented_precond_candidates = [from_hash(hp) for hp in augmented_precond_candidates]
        for j, init_state in enumerate(augmented_precond_candidates):
            lines_program = lines_program_orig.copy()
            executable = False
            max_iter = 0
            while not executable and max_iter < 10 and lines_program is not None:        
                message = check_programs.check_script(
                        lines_program, 
                        init_state, 
                        '../example_graphs/TrimmedTestScene6_graph.json')
                if message is None:
                    lines_program = None
                    continue
                lines_program = [x.strip() for x in lines_program]
                
                if 'is executable' not in message:
                    lines_program = exception_handler.correctedProgram(
                            lines_program, init_state, message, verbose)
                    max_iter += 1
                else:
                    executable = True

            if executable and max_iter > 0:
                if verbose:
                    print(colored(
                        'Program modified in {} exceptions'.format(max_iter), 
                        'green'))        
                augmented_preconds_i.append(str(init_state))
                augmented_progs_i.append(lines_program)
            elif not executable:
                if verbose:
                    print(colored('Program not solved', 'red'))

        if write_augment_data:
            write_data(program, augmented_progs_i)
            write_precond(program, augmented_preconds_i)

num_processes = 50
processes = []
manager = Manager()
programs_done = manager.dict()
for m in range(num_processes):
    p = Process(target=augment_dataset, args=(programs_done, programs))
    p.start()
    processes.append(p)


for p in processes:
    p.join()
