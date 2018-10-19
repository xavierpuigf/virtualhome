import glob
import shutil
import os
import json
import exception_handler
import ipdb
import re
from collections import Counter
import sys
from termcolor import colored

sys.path.append('..')
import check_programs

dump_results = True

prog_folder = 'programs_processed_precond_nograb_morepreconds_executable_perturbed'
prog_folder_out = 'programs_processed_precond_nograb_morepreconds_executable_perturbed_solved'
programs = glob.glob('{}/withoutconds/*/*.txt'.format(prog_folder))


errors = []
titles = []
cont = 0
for program in programs:

    #print elem
    #print content[elem]
    state_file = program.replace('withoutconds', 'initstate').replace('.txt', '.json')

    with open(program, 'r') as f:
        lines_program = f.readlines()
        
    with open(state_file, 'r') as f:
        init_state = json.load(f)

    executable = False
    max_iter = 0
    while not executable and max_iter < 10 and lines_program is not None:
        
        message = check_programs.check_script(lines_program, 
                                              init_state, 
                                              '../example_graphs/TrimmedTestScene6_graph.json')
        
        
        lines_program = [x.strip() for x in lines_program]
        
        if 'is executable' not in message:
            lines_program = exception_handler.correctedProgram(lines_program, init_state, message)
            max_iter += 1
        else:
            executable = True

    if executable and max_iter > 0:
        print(colored('Program modified in {} exceptions'.format(max_iter), 'green'))
        
        if dump_results:
            prog_out = program.replace(prog_folder, prog_folder_out)
            state_out = prog_out.replace('.txt', '.json').replace('withoutconds', 'initstate')
            if not os.path.isdir(os.path.dirname(prog_out)):
                os.makedirs(os.path.dirname(prog_out))
                os.makedirs(os.path.dirname(state_out))
                with open(state_out, 'w+') as f:
                    f.write(json.dumps(init_state))
                with open(prog_out, 'w+') as f:
                    f.writelines([x+'\n' for x in lines_program])
    elif not executable:
        print(colored('Program not solved', 'red'))

    #file_input = elem.replace('/Users/andrew/UofT/home_sketch2program/data/', '').replace('withoutconds', 'withconds')
    #with open(file_input, 'r') as f:
    #	aux = f.readlines()
    #print (''.join(aux))
    #print '\n'
    #ipdb.set_trace()
    #print '\n'


#print('Reasons failure')
#for el in cnt:
#    print(el)
#
#
#cnt = Counter(titles).most_common()
#print('Titles')
#for el in cnt:
#    print(el)
