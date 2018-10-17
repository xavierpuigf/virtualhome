# Perturbate the executable programs
import glob
import os
import json
import shutil 
import pdb
import random

prob_modif = 0.3

file_in = 'programs_processed_precond_nograb_morepreconds'
file_out = 'programs_processed_precond_nograb_morepreconds_executable_perturbed'

with open('..//executable_info.json', 'r') as f:
    content = json.load(f)

for elem in content:
    elem_modif = ' '.join(content[elem].split()[1:])
    if 'Script is executable' in elem_modif:
        file = elem.replace('dataset_augmentation/', '')
        init_state_file = file.replace('withoutconds', 'initstate').replace('.txt', '.json')

        file_out_program = file.replace(file_in, file_out)
        file_out_state = init_state_file.replace(file_in, file_out)

        if not os.path.isdir(os.path.dirname(file_out_program)):
            os.makedirs(os.path.dirname(file_out_program))

        if not os.path.isdir(os.path.dirname(file_out_state)):
            os.makedirs(os.path.dirname(file_out_state))

        with open(init_state_file, 'r') as f:
            modified_state = json.load(f)

        # Remove sitting
        modified_state = [x for x in modified_state if list(x)[0] != 'sitting' or random.random() > prob_modif] 

        # Remove at reach
        modified_state = [x for x in modified_state if list(x)[0] != 'atreach' or random.random() > prob_modif]  

        # Turn is closed to is open
        for i, cond in enumerate(modified_state):
            if list(cond)[0] == 'closed':
                modified_state[i] = {'open': cond['closed']}    

        shutil.copy(file, file_out_program)
        with open(file_out_state, 'w+') as f:
            f.write(json.dumps(modified_state))