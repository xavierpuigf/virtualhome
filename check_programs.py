import os
import sys
import json
import utils
import glob
import random
import numpy as np
from tqdm import tqdm
from shutil import copyfile
from joblib import Parallel, delayed

from execution import Relation, State
from scripts import read_script, read_script_from_string, read_script_from_list_string, ScriptParseException
from execution import ScriptExecutor
from environment import EnvironmentGraph, Room


random.seed(123)
verbose = True
dump = True
max_nodes = 300


def dump_one_data(txt_file, script, graph_state_list, id_mapping, graph_path):

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


    # read old program
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


def translate_graph_dict(path):

    graph_dict = utils.load_graph_dict(path)
    properties_data = utils.load_properties_data(file_name='resources/object_script_properties_data.json')
    node_list = [node["class_name"] for node in graph_dict['nodes']]

    static_objects = ['bathroom', 'floor', 'wall', 'ceiling', 'rug', 'curtains', 'ceiling_lamp', 'wall_lamp', 
                        'bathroom_counter', 'bathtub', 'towel_rack', 'wall_shelf', 'stall', 'bathroom_cabinet', 
                        'toilet', 'shelf', 'door', 'doorjamb', 'window', 'lightswitch', 'bedroom', 'table_lamp', 
                        'chair', 'bookshelf', 'nightstand', 'bed', 'closet', 'coatrack', 'coffee_table', 
                        'pillow', 'hanger', 'character', 'kitchen', 'maindoor', 'tv_stand', 'kitchen_table', 
                        'bench', 'kitchen_counter', 'sink', 'power_socket', 'tv', 'clock', 'wall_phone', 
                        'cutting_board', 'stove', 'oventray', 'toaster', 'fridge', 'coffeemaker', 'microwave', 
                        'livingroom', 'sofa', 'coffee_table', 'desk', 'cabinet', 'standing_mirror', 'globe', 
                        'mouse', 'mousemat', 'cpu_screen', 'cpu_case', 'keyboard', 'ceilingfan', 
                        'kitchen_cabinets', 'dishwasher', 'cookingpot', 'wallpictureframe', 'vase', 'knifeblock', 
                        'stovefan', 'orchid', 'long_board', 'garbage_can', 'photoframe', 'balance_ball', 'closet_drawer']

    new_nodes = [i for i in filter(lambda v: v["class_name"] in static_objects, graph_dict['nodes'])]
    trimmed_nodes = [i for i in filter(lambda v: v["class_name"] not in static_objects, graph_dict['nodes'])]

    available_id = [i["id"] for i in filter(lambda v: v["class_name"] in static_objects, graph_dict['nodes'])]

    new_edges = [i for i in filter(lambda v: v['to_id'] in available_id and v['from_id'] in available_id, graph_dict['edges'])]

    # change the object name 
    script_object2unity_object = utils.load_name_equivalence()
    unity_object2script_object = {}
    for k, vs in script_object2unity_object.items():
        unity_object2script_object[k] = k
        for v in vs:
            unity_object2script_object[v] = k

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
    
    translated_path = path.replace('TestScene', 'TrimmedTestScene')
    json.dump({"nodes": new_nodes_script_object, "edges": new_edges, "trimmed_nodes": trimmed_nodes}, open(translated_path, 'w'))
    return translated_path


def check_script(program_str, precond, graph_path, inp_graph_dict=None, id_mapping={}, info={}):

    properties_data = utils.load_properties_data(file_name='../resources/object_script_properties_data.json')
    object_states = json.load(open('../resources/object_states.json'))
    object_placing = json.load(open('../resources/object_script_placing.json'))

    helper = utils.graph_dict_helper(properties_data, object_placing, object_states, max_nodes)

    #helper.initialize()
    try:
        script = read_script_from_list_string(program_str)
    except ScriptParseException:
        # print("Can not parse the script")
        return None, None, None, None, None
    
    if inp_graph_dict is None:
        graph_dict = utils.load_graph_dict(graph_path)
    else:
        graph_dict = inp_graph_dict
    message, executable, final_state, graph_state_list, id_mapping, info = check_one_program(
        helper, script, precond, graph_dict, w_graph_list=True, modify_graph=(inp_graph_dict is None), id_mapping=id_mapping, **info)

    return message, final_state, graph_state_list, graph_dict, id_mapping, info, helper


def check_one_program(helper, script, precond, graph_dict, w_graph_list, modify_graph=True, id_mapping={}, **info):

    for p in precond:
        for k, vs in p.items():
            if isinstance(vs[0], list): 
                for v in vs:
                    v[0] = v[0].lower().replace(' ', '_')
            else:
                v = vs
                v[0] = v[0].lower().replace(' ', '_')

    helper.initialize(graph_dict)
    if modify_graph:
        ## add missing object from scripts (id from 1000) and set them to default setting
        ## id mapping can specify the objects that already specify in the graphs
        helper.set_to_default_state(graph_dict, None, id_checker=lambda v: True)


        id_mapping, first_room, room_mapping = helper.add_missing_object_from_script(script, precond, graph_dict, id_mapping)
        info = {'room_mapping': room_mapping}
        objects_id_in_script = [v for v in id_mapping.values()]
        helper.set_to_default_state(graph_dict, first_room, id_checker=lambda v: v in objects_id_in_script)

        ## place the random objects (id from 2000)
        max_node_to_place = max_nodes - len(graph_dict["nodes"])
        n = random.randint(max_node_to_place - 20, max_node_to_place)
        helper.add_random_objs_graph_dict(graph_dict, n=max(n, 0))
        helper.set_to_default_state(graph_dict, None, id_checker=lambda v: v >= 2000)
        helper.random_change_object_state(id_mapping, graph_dict, id_checker=lambda v: v not in objects_id_in_script)

        ## set relation and state from precondition
        helper.prepare_from_precondition(precond, id_mapping, graph_dict)
        helper.open_all_doors(graph_dict)
        helper.ensure_light_on(graph_dict, id_checker=lambda v: v not in objects_id_in_script)
        helper.check_binary(graph_dict)
        
        assert len(graph_dict["nodes"]) <= max_nodes
    
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

    return message, executable, final_state, graph_state_list, id_mapping, info


def joblib_one_iter(inp):

    txt_file, graph_path = inp
    
    properties_data = utils.load_properties_data(file_name='resources/object_script_properties_data.json')
    object_states = json.load(open('resources/object_states.json'))
    object_placing = json.load(open('resources/object_script_placing.json'))

    helper = utils.graph_dict_helper(properties_data, object_placing, object_states, max_nodes)
    
    try:
        script = read_script(txt_file)
    except ScriptParseException:
        return None, None, None, None, None

    precond_path = txt_file.replace('withoutconds', 'initstate').replace('txt', 'json')


    graph_dict = utils.load_graph_dict(graph_path)

    precond = json.load(open(precond_path))
    message, executable, _, graph_state_list, id_mapping, _ = check_one_program(helper, script, precond, graph_dict, w_graph_list=True)
    if executable and dump:
        dump_one_data(txt_file, script, graph_state_list, id_mapping, graph_path)

    return script, message, executable, graph_state_list, id_mapping


def check_whole_set(dir_path, graph_path):

    """Use precondition to modify the environment graphs
    """

    program_dir = os.path.join(dir_path, 'withoutconds')
    program_txt_files = glob.glob(os.path.join(program_dir, '*/*.txt'))
    
    joblib_one_iter(['programs_processed_precond_nograb_morepreconds/withoutconds/results_text_rebuttal_specialparsed_programs_upworknturk_second/split36_1.txt', graph_path[0]])

    executable_programs = 0
    not_parsable_programs = 0
    executable_program_length = []
    not_executable_program_length = []
    if isinstance(graph_path, list):
        multiple_graphs = True
        executable_scene_hist = {p: 0 for p in graph_path}
    else: 
        multiple_graphs = False

    info = {}

    joblib_inputs = []
    n = len(program_txt_files) // 30
    program_txt_files = np.array(program_txt_files)
    for txt_files in np.array_split(program_txt_files, n):
        
        if multiple_graphs:
            joblib_inputs = []
            for f in txt_files:
                random.shuffle(graph_path)
                for g in graph_path[:3]:
                    joblib_inputs.append([f, g])
        else:
            joblib_inputs = [[f, graph_path] for f in txt_files]
        
        print("Running on simulators")
        results = Parallel(n_jobs=os.cpu_count())(delayed(joblib_one_iter)(inp) for inp in joblib_inputs)
        #results = [joblib_one_iter(inp) for inp in joblib_inputs]
        for k, (input, result) in enumerate(zip(joblib_inputs, results)):
            i_txt_file, i_graph_path = input
            script, message, executable, _, _ = result
            if script is None:
                not_parsable_programs += 1
                continue

            if executable:
                executable_programs += 1
                if multiple_graphs:
                    executable_scene_hist[i_graph_path] += 1
                executable_program_length.append(len(script))
            else:
                not_executable_program_length.append(len(script))

            if verbose:
                print(k, message)

            if i_txt_file not in info:
                info[i_txt_file] = []
            info[i_txt_file].append({"message": message, "graph_path": i_graph_path})

    if multiple_graphs:
        info['scene_hist'] = executable_scene_hist
        print(executable_scene_hist)

    print("Total programs: {}, executable programs: {}".format(len(program_txt_files), executable_programs))
    print("{} programs can not be parsed".format(not_parsable_programs))

    executable_program_length = sum(executable_program_length) / len(executable_program_length)
    not_executable_program_length = sum(not_executable_program_length) / len(not_executable_program_length)
    info["executable_prog_len"] = executable_program_length
    info["non_executable_prog_len"] = not_executable_program_length
    print("Executable program average length: {:.2f}, not executable program average length: {:.2f}".format(executable_program_length, not_executable_program_length))
    json.dump(info, open("{}/executable_info.json".format('programs_all_graphs3'), 'w'))


def check_executability(string, graph_dict):

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
        translated_path = ['example_graphs/TrimmedTestScene7_graph.json']
    else:
        translated_path = ['example_graphs/TrimmedTestScene{}_graph.json'.format(i+1) for i in range(6)]
    print(translated_path)
    #translated_path = translate_graph_dict(path='example_graphs/TestScene6_graph.json')
    check_whole_set('{}/programs_processed_precond_nograb_morepreconds'.format('programs_all_graphs3'), graph_path=translated_path)
