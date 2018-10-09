import os
import json
import utils
import glob
from tqdm import tqdm

from execution import Relation, State
from scripts import read_script, read_precond, ScriptParseException
from execution import ScriptExecutor
from environment import EnvironmentGraph
import ipdb


def print_node_names(n_list):
    if len(n_list) > 0:
        print([n.class_name for n in n_list])


def check(dir_path):

    program_dir = os.path.join(dir_path, 'withoutconds')
    program_txt_files = glob.glob(os.path.join(program_dir, '*/*.txt'))


    for txt_file in tqdm(program_txt_files):
        try:
            script = read_script(txt_file)
        except ScriptParseException:
            continue
            
        precond = read_precond(txt_file.replace('withoutconds', 'initstate').replace('txt', 'json'))
        properties_data = utils.load_properties_data(file_name='resources/object_script_properties_data.json')
        graph_dict = utils.create_graph_dict_from_precond(script, precond, properties_data)

        '''
        # load object placing
        object_placing = utils.load_object_placing(file_name='resources/object_script_placing.json')
        # add random objects
        utils.perturb_graph_dict(graph_dict, object_placing, properties_data, n=10)
        '''
        
        name_equivalence = utils.load_name_equivalence()

        graph = EnvironmentGraph(graph_dict)
        executor = ScriptExecutor(graph, name_equivalence)
        state = executor.execute(script)

        if state is None:
            print('Script is not executable, since {}'.format(executor.info.get_error_string()))
        else:
            print('Script is executable')
    

if __name__ == '__main__':
    check('/Users/andrew/UofT/instance_programs_processed_precond_nograb')