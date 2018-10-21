import glob
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
    augmented_data_dir = 'augmented_program_exception'
    if not os.path.exists(augmented_data_dir):
        os.makedirs(augmented_data_dir)

prog_folder = 'programs_processed_precond_nograb_morepreconds'
programs = glob.glob('{}/withoutconds/*/*.txt'.format(prog_folder))


cont = 0

def augment_dataset(d, programs):
    programs = np.random.permutation(programs).tolist()
    for program in programs:
        if program in d.keys(): 
            continue
        d[program] = str(current_process())
        print(len(d.keys()))
        state_file = program.replace(
                'withoutconds', 'initstate').replace('.txt', '.json')

        with open(program, 'r') as f:
            lines_program = f.readlines()
            
        with open(state_file, 'r') as f:
            init_state = json.load(f)

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
            if write_augment_data:
                prog_out = program.replace(prog_folder, augmented_data_dir)
                state_out = prog_out.replace(
                        '.txt', '.json').replace('withoutconds', 'initstate')
                if not os.path.isdir(os.path.dirname(prog_out)):
                    os.makedirs(os.path.dirname(prog_out))
                    os.makedirs(os.path.dirname(state_out))
                    with open(state_out, 'w+') as f:
                        f.write(json.dumps(init_state))
                    with open(prog_out, 'w+') as f:
                        f.writelines([x+'\n' for x in lines_program])
        elif not executable:
            if verbose:
                print(colored('Program not solved', 'red'))


num_processes = 10
processes = []
manager = Manager()
programs_done = manager.dict()
for m in range(num_processes):
    p = Process(target=augment_dataset, args=(programs_done, programs))
    p.start()
    processes.append(p)


for p in processes:
    p.join()
