import os
import sys
import json
import random
import numpy as np
from glob import glob
from termcolor import colored
from tqdm import tqdm
from multiprocessing import Pool

from . import utils
from .scripts import read_script, read_script_from_string, read_script_from_list_string, ScriptParseException
from .execution import ScriptExecutor
from .environment import EnvironmentGraph


random.seed(123)
verbose = True
dump = True
multi_process = True
num_process = os.cpu_count()
max_nodes = 500


def dump_one_data(txt_file, script, graph_state_list, id_mapping, graph_path):
    """
        Writes the graphs into files
    """
    new_path = txt_file.replace('withoutconds', 'executable_programs')
    graph_sub_dir = graph_path.split('/')[-1].replace('.json', '')
    new_path = new_path.split('/')
    j = new_path.index('executable_programs') + 1
    new_path = new_path[:j] + [graph_sub_dir] + new_path[j:]
    new_path = '/'.join(new_path)
    new_dir = os.path.dirname(new_path)

    if not os.path.exists(new_dir):
        try:
            os.makedirs(new_dir)
        except FileExistsError:
            pass

    old_f = open(txt_file, 'r')
    old_program = old_f.read()
    old_f.close()

    new_f = open(new_path, 'w')
    
    prefix = old_program.split('\n\n\n')[0]
    new_f.write(prefix)
    new_f.write('\n\n\n')

    for script_line in script:
        script_line_str = '[{}]'.format(script_line.action.name)
        if script_line.object():
            script_line_str += ' <{}> ({})'.format(script_line.object().name, script_line.object().instance)
        if script_line.subject():
            script_line_str += ' <{}> ({})'.format(script_line.subject().name, script_line.subject().instance)

        for k, v in id_mapping.items():
            obj_name, obj_number = k
            id = v
            script_line_str = script_line_str.replace('<{}> ({})'.format(obj_name, id), '<{}> ({}.{})'.format(obj_name, obj_number, id))
        
        new_f.write(script_line_str)
        new_f.write('\n')

    # init graph and final graph
    new_path = txt_file.replace('withoutconds', 'init_and_final_graphs').replace('txt', 'json')
    graph_sub_dir = graph_path.split('/')[-1].replace('.json', '')
    new_path = new_path.split('/')
    j = new_path.index('init_and_final_graphs') + 1
    new_path = new_path[:j] + [graph_sub_dir] + new_path[j:]
    new_path = '/'.join(new_path)
    new_dir = os.path.dirname(new_path)
    if not os.path.exists(new_dir):
        try:
            os.makedirs(new_dir)
        except FileExistsError:
            pass

    new_f = open(new_path, 'w')
    json.dump({"init_graph": graph_state_list[0], "final_graph": graph_state_list[-1]}, new_f)
    new_f.close()

    # state list
    new_path = txt_file.replace('withoutconds', 'state_list').replace('txt', 'json')
    graph_sub_dir = graph_path.split('/')[-1].replace('.json', '')
    new_path = new_path.split('/')
    j = new_path.index('state_list') + 1
    new_path = new_path[:j] + [graph_sub_dir] + new_path[j:]
    new_path = '/'.join(new_path)
    new_dir = os.path.dirname(new_path)
    if not os.path.exists(new_dir):
        try:
            os.makedirs(new_dir)
        except FileExistsError:
            pass

    new_f = open(new_path, 'w')
    json.dump({"graph_state_list": graph_state_list}, new_f)
    new_f.close()


def translate_graph_dict_nofile(graph_dict):

    abs_dir_path = os.path.dirname(os.path.abspath(__file__))

    file_name = os.path.join(abs_dir_path, '../../resources/properties_data.json')
    properties_data = utils.load_properties_data(file_name=file_name)

    static_objects = ['bathroom', 'floor', 'wall', 'ceiling', 'rug', 'curtains', 'ceiling_lamp', 'wall_lamp', 
                        'bathroom_counter', 'bathtub', 'towel_rack', 'wall_shelf', 'stall', 'bathroom_cabinet', 
                        'toilet', 'shelf', 'door', 'doorjamb', 'window', 'lightswitch', 'bedroom', 'table_lamp', 
                        'chair', 'bookshelf', 'nightstand', 'bed', 'closet', 'coatrack', 'coffee_table', 
                        'pillow', 'hanger', 'character', 'kitchen', 'maindoor', 'tv_stand', 'kitchen_table', 
                        'bench', 'kitchen_counter', 'sink', 'power_socket', 'tv', 'clock', 'wall_phone', 
                        'cutting_board', 'stove', 'oventray', 'toaster', 'fridge', 'coffeemaker', 'microwave', 
                        'livingroom', 'sofa', 'coffee_table', 'desk', 'cabinet', 'standing_mirror', 'globe', 
                        'mouse', 'mousemat', 'cpu_screen', 'computer', 'cpu_case', 'keyboard', 'ceilingfan', 
                        'kitchen_cabinets', 'dishwasher', 'cookingpot', 'wallpictureframe', 'vase', 'knifeblock', 
                        'stovefan', 'orchid', 'long_board', 'garbage_can', 'photoframe', 'balance_ball', 'closet_drawer', 'faucet']

    static_objects = static_objects + [x.replace('_', '') for x in static_objects]

    new_nodes = [i for i in filter(lambda v: v["class_name"] in static_objects, graph_dict['nodes'])]
    trimmed_nodes = [i for i in filter(lambda v: v["class_name"] not in static_objects, graph_dict['nodes'])]

    available_id = [i["id"] for i in filter(lambda v: v["class_name"] in static_objects, graph_dict['nodes'])]

    new_edges = [i for i in filter(lambda v: v['to_id'] in available_id and v['from_id'] in available_id, graph_dict['edges'])]

    # change the object name 
    script_object2unity_object = utils.load_name_equivalence()
    unity_object2script_object = utils.build_unity2object_script(script_object2unity_object)

    new_nodes_script_object = []
    for node in new_nodes:
        class_name = unity_object2script_object[node["class_name"]].lower().replace(' ', '_') if node["class_name"] in unity_object2script_object else node["class_name"].lower().replace(' ', '_')
        
        new_nodes_script_object.append({
            "properties": [i.name for i in properties_data[class_name]] if class_name in properties_data else node["properties"], 
            "id": node["id"], 
            "states": node["states"], 
            "category": node["category"], 
            "class_name": class_name
        })
    return {"nodes": new_nodes_script_object, "edges": new_edges, 'trimmed_nodes': trimmed_nodes}

def translate_graph_dict(path):
    """
        Changes the object names and properties of an environment graph so that 
        they match with the names in the scripts. 
    """
    graph_dict = utils.load_graph_dict(path)
    trimmed_graph = translate_graph_dict_nofile(graph_dict)
    translated_path = path.replace('TestScene', 'TrimmedTestScene')
    json.dump(trimmed_graph, open(translated_path, 'w+'))
    return translated_path


def check_one_program(helper, script, precond, graph_dict, w_graph_list, modify_graph=True, place_other_objects=True, id_mapping={}, **info):

    helper.initialize(graph_dict)
    script, precond = modify_objects_unity2script(helper, script, precond)

    if modify_graph:
        ## add missing object from scripts (id from 1000) and set them to default setting
        ## id mapping can specify the objects that already specify in the graphs
        helper.set_to_default_state(graph_dict, None, id_checker=lambda v: True)
        id_mapping, first_room, room_mapping = helper.add_missing_object_from_script(script, precond, graph_dict, id_mapping)
        
        info = {'room_mapping': room_mapping}
        objects_id_in_script = [v for v in id_mapping.values()]
        helper.set_to_default_state(graph_dict, first_room, id_checker=lambda v: v in objects_id_in_script)

        ## place the random objects (id from 2000)
        if place_other_objects:
            max_node_to_place = max_nodes - len(graph_dict["nodes"])
            n = random.randint(max_node_to_place - 20, max_node_to_place)
            helper.add_random_objs_graph_dict(graph_dict, n=max(n, 0))
            helper.set_to_default_state(graph_dict, None, id_checker=lambda v: v >= 2000)
            helper.random_change_object_state(id_mapping, graph_dict, id_checker=lambda v: v not in objects_id_in_script)

        ## set relation and state from precondition
        helper.check_binary(graph_dict, id_checker=lambda v: True, verbose=False)
        random_objects_id = helper.random_objects_id
        helper.prepare_from_precondition(precond, id_mapping, graph_dict)

        helper.open_all_doors(graph_dict)
        helper.ensure_light_on(graph_dict, id_checker=lambda v: v not in objects_id_in_script)
        
        helper.check_binary(graph_dict, id_checker=lambda v: v >= random_objects_id, verbose=False)
        helper.check_binary(graph_dict, id_checker=lambda v: True, verbose=True)
        
        assert len(graph_dict["nodes"]) <= max_nodes, 'Max nodes: {}. Current Nodes {}'.format(len(graph_dict['nodes']), max_nodes)
    
    elif len(id_mapping) != 0:
        # Assume that object mapping specify all the objects in the scripts
        helper.modify_script_with_specified_id(script, id_mapping, **info)

    graph = EnvironmentGraph(graph_dict)
    name_equivalence = utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    executable, final_state, graph_state_list = executor.execute(script, w_graph_list=w_graph_list)

    if executable:
        message = 'Script is executable'
    else:
        message = 'Script is not executable, since {}'.format(executor.info.get_error_string())

    return message, executable, final_state, graph_state_list, id_mapping, info, script


def check_script(program_str, precond, graph_path, inp_graph_dict=None, 
                 modify_graph=True, id_mapping={}, info={}):

    helper = utils.graph_dict_helper(max_nodes=max_nodes)
    
    try:
        script = read_script_from_list_string(program_str)
    except ScriptParseException:
        return None, None, None, None, None, None, None, None

    if inp_graph_dict is None:
        graph_dict = utils.load_graph_dict(graph_path)
    else:
        graph_dict = inp_graph_dict
    message, executable, final_state, graph_state_list, id_mapping, info, modif_script = check_one_program(
        helper, script, precond, graph_dict, w_graph_list=True, modify_graph=modify_graph,
        id_mapping=id_mapping, place_other_objects=True, **info)

    return message, final_state, graph_state_list, graph_dict, id_mapping, info, helper, modif_script


def check_original_script(inp):
    """ 
    Checks if a script is executable in a graph environment
    Given a script and a graph. Infers script preconditions modifies the graph
    and checks whether the script can be executed.
    :param inp. Script path and Graph path where the script will be executed
    """
    txt_file, graph_path = inp

    helper = utils.graph_dict_helper(max_nodes=max_nodes)
    
    try:
        script = read_script(txt_file)
    except ScriptParseException:
        return None, None, None, None, None

    precond_path = txt_file.replace('withoutconds', 'initstate').replace('txt', 'json')

    graph_dict = utils.load_graph_dict(graph_path)

    precond = json.load(open(precond_path))

    message, executable, _, graph_state_list, id_mapping, _, _ = check_one_program(helper, script, precond, graph_dict, w_graph_list=True)
    if executable and dump:
        dump_one_data(txt_file, script, graph_state_list, id_mapping, graph_path)

    return script, message, executable, graph_state_list, id_mapping


def modify_objects_unity2script(helper, script=[], precond=[]):
    """Convert the script and precond's objects to match unity programs
    """
    for script_line in script:
        for param in script_line.parameters:
            if param.name in helper.unity_object2script_object:
                param.name = helper.unity_object2script_object[param.name]

    for p in precond:
        for k, vs in p.items():
            if isinstance(vs[0], list): 
                for v in vs:
                    v[0] = v[0].lower().replace(' ', '_')
                    if v[0] in helper.unity_object2script_object:
                        v[0] = helper.unity_object2script_object[v[0]]
            else:
                v = vs
                v[0] = v[0].lower().replace(' ', '_')
                if v[0] in helper.unity_object2script_object:
                    v[0] = helper.unity_object2script_object[v[0]]
            
    return script, precond


def check_whole_set(dir_path, graph_path):

    """Use precondition to modify the environment graphs
    """

    program_dir = os.path.join(dir_path, 'withoutconds')
    program_txt_files = glob(os.path.join(program_dir, '*/*.txt'))
    executable_programs = []
    not_parsable_programs = []
    executable_program_length = []
    not_executable_program_length = []
    if isinstance(graph_path, list):
        multiple_graphs = True
        executable_scene_hist = {p: 0 for p in graph_path}
    else: 
        multiple_graphs = False

    info = {}
    if os.path.isfile('data/executable_info.json'):
        with open('data/executable_info.json', 'r') as f:
            info = json.load(f)
    n = max(len(program_txt_files) // (num_process*4), 1)
    program_txt_files = np.array(program_txt_files)
    pool = Pool(processes=num_process)
    for txt_files in tqdm(np.array_split(program_txt_files, n)):
        
        if multiple_graphs:
            # Distribute programs across different graphs. Every program is executed by 3 graphs
            mp_inputs = []
            for f in txt_files:
                random.shuffle(graph_path)
                for g in graph_path[:3]:
                    mp_inputs.append([f, g])
        else:
            mp_inputs = [[f, graph_path] for f in txt_files]
        
        if multi_process:
            results = pool.map(check_original_script, mp_inputs)
        else:
            results = [check_original_script(inp) for inp in mp_inputs]

        for input, result in zip(mp_inputs, results):
            i_txt_file, i_graph_path = input
            script, message, executable, _, _ = result
            if script is None:
                not_parsable_programs.append(i_txt_file)
                continue

            if executable:
                executable_programs.append(i_txt_file)
                if multiple_graphs:
                    executable_scene_hist[i_graph_path] += 1
                executable_program_length.append(len(script))
            else:
                not_executable_program_length.append(len(script))

            if verbose and message != "Script is executable":
                print(i_txt_file)
                print(i_graph_path)
                print(colored(message, "cyan"))
                
            if i_txt_file not in info:
                info[i_txt_file] = []
            info[i_txt_file].append({"message": message, "graph_path": i_graph_path})

    if multiple_graphs:
        info['scene_hist'] = executable_scene_hist
        print(executable_scene_hist)

    print("Total programs: {}, executable programs: {} (unique: {})".format(len(program_txt_files), len(executable_programs), len(set(executable_programs))))
    print("Programs that can not be parsed: {} (unique: {})".format(len(not_parsable_programs), len(set(not_parsable_programs))))
    if len(executable_program_length):
        executable_program_length = sum(executable_program_length) / len(executable_program_length)
    else:
        executable_program_length = 0.

    if len(not_executable_program_length):
        not_executable_program_length = sum(not_executable_program_length) / len(not_executable_program_length)
    else:
        not_executable_program_length = 0.

    info["executable_prog_len"] = executable_program_length
    info["non_executable_prog_len"] = not_executable_program_length
    print("Executable program average length: {:.2f}, not executable program average length: {:.2f}".format(executable_program_length, not_executable_program_length))
    json.dump(info, open("data/executable_info.json", 'w'))


def check_executability(input):

    script, graph_dict = input
    if len(script.split(', ')) == 1:
        final_state = graph_dict
        return True, True, final_state

    string = modify_script(script)

    able_to_be_parsed = False
    able_to_be_executed = False
    try:
        script = read_script_from_string(string)
        able_to_be_parsed = True
    except ScriptParseException:
        return able_to_be_parsed, able_to_be_executed, None

    graph = EnvironmentGraph(graph_dict)
    name_equivalence = utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    try:
        executable, final_state, _ = executor.execute(script)
    except AttributeError:
        print("Attribute error")
        print("Program:")
        programs = string.split(', ')
        for p in programs:
            print(p)
        return able_to_be_parsed, able_to_be_executed, None
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print("Program:")
        programs = string.split(', ')
        for p in programs:
            print(p)
        return able_to_be_parsed, able_to_be_executed, None

    if executable:
        able_to_be_executed = True
        return able_to_be_parsed, able_to_be_executed, final_state.to_dict()
    else:
        return able_to_be_parsed, able_to_be_executed, None


def modify_script(script):

    modif_script = []
    for script_line in script.split(', '):
        action, object_name, object_i, subject_name, subject_i = script_line.split(' ')
        if object_name in ['<<none>>', '<<eos>>']:
            modif_script.append(action)
        elif subject_name in ['<<none>>', '<<eos>>']:
            modif_script.append('{} {} {}'.format(action, object_name, object_i))
        else:
            modif_script.append('{} {} {} {} {}'.format(action, object_name, object_i, subject_name, subject_i))

    return ', '.join(modif_script)


if __name__ == '__main__':
    cont = sys.argv[1]
    if int(cont) == 0:
        translated_path = translate_graph_dict(path='example_graphs/TestScene7_graph.json')
        translated_path = ['example_graphs/TrimmedTestScene7_graph.json']
    else:
        translated_path = [translate_graph_dict(path='example_graphs/TestScene{}_graph.json'.format(i+1)) for i in range(6)]
        translated_path = ['example_graphs/TrimmedTestScene{}_graph.json'.format(i+1) for i in range(6)]
    programs_dir = 'data/input_scripts_preconds_release/programs_processed_precond_nograb_morepreconds'
    check_whole_set(programs_dir, graph_path=translated_path)
