# Perturbate the executable programs
import glob
import os
import json
import shutil 
import pdb
import random
import glob
import shutil
import os
import json
import exception_handler
import ipdb
import re
from collections import Counter
import sys
from tqdm import tqdm
from termcolor import colored
sys.path.append('..')
import check_programs


dump_results = True
prob_modif = 0.8
programs_new, programs_executable = 0, 0

file_in = 'programs_processed_precond_nograb_morepreconds'
file_out = 'programs_processed_precond_nograb_morepreconds_executable_perturbed'

with open('..//executable_info.json', 'r') as f:
    content = json.load(f)

for elem in tqdm(content):
    elem_modif = ' '.join(content[elem].split()[1:])
    if 'Script is executable' in elem_modif:
        programs_executable
        file = elem.replace('dataset_augmentation/', '')
        init_state_file = file.replace('withoutconds', 'initstate').replace('.txt', '.json')

        file_out_program = file.replace(file_in, file_out)
        file_out_state = init_state_file.replace(file_in, file_out)

        
        with open(init_state_file, 'r') as f:
            modified_state = json.load(f)

        prev_state = modified_state.copy()
        
        # Remove sitting
        modified_state = [x for x in modified_state if list(x)[0] != 'sitting' or random.random() > prob_modif]

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


        # TODO: besides removing and swapping preconds, add new preconds depending on the properties of the environment


        init_state = modified_state
        with open(file, 'r') as f:
            lines_program = f.readlines()

        executable = False
        max_iter = 0

        while not executable and max_iter < 10 and lines_program is not None:
            message = check_programs.check_script(lines_program, 
                                                  init_state, 
                                                  '../example_graphs/TrimmedTestScene6_graph.json')
            
            
            lines_program = [x.strip() for x in lines_program]
            #print(message)
            if 'is executable' not in message:
                lines_program = exception_handler.correctedProgram(lines_program, init_state, message)
                max_iter += 1
            else:
                executable = True

        if executable and max_iter > 0:
            print(colored('Program modified in {} exceptions'.format(max_iter), 'green'))
            programs_new += 1
            if dump_results:
                #prog_out = program.replace(prog_folder, prog_folder_out)
                #state_out = prog_out.replace('.txt', '.json').replace('withoutconds', 'initstate')

                if not os.path.exists(os.path.dirname(file_out_program)):
                    os.makedirs(os.path.dirname(file_out_program))
                if not os.path.exists(os.path.dirname(file_out_state)):
                    os.makedirs(os.path.dirname(file_out_state))
                    
                with open(file_out_state, 'w+') as f:
                    f.write(json.dumps(init_state))
                with open(file_out_program, 'w+') as f:
                    f.writelines([x+'\n' for x in lines_program])
        elif not executable:
            print(colored('Program not solved', 'red'))

print(programs_new, programs_executable)