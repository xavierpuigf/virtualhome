import os
import json
import utils
import glob
import copy
import random
from tqdm import tqdm

from execution import Relation, State
from scripts import read_script, read_precond, ScriptParseException
from execution import ScriptExecutor
from environment import EnvironmentGraph, Room
import ipdb


random.seed(123)

def print_node_names(n_list):
    if len(n_list) > 0:
        print([n.class_name for n in n_list])


def translate_graph_dict():

    path = 'example_graphs/TestScene6_graph.json'
    graph_dict = utils.load_graph_dict(path)
    node_list = [node["class_name"] for node in graph_dict['nodes']]

    static_objects = ['bathroom', 'floor', 'wall', 'ceiling', 'rug', 'curtains', 'ceiling_lamp', 'wall_lamp', 
                        'bathroom_counter', 'bathtub', 'towel_rack', 'wall_shelf', 'stall', 'bathroom_cabinet', 
                        'toilet', 'shelf', 'door', 'doorjamb', 'window', 'lightswitch', 'bedroom', 'table_lamp', 
                        'chair', 'bookshelf', 'nightstand', 'bed', 'closet', 'coatrack', 'coffee_table', 
                        'pillow', 'hanger', 'character', 'kitchen', 'maindoor', 'tv_stand', 'kitchen_table', 
                        'bench', 'kitchen_counter', 'sink', 'power_socket', 'tv', 'clock', 'wall_phone', 
                        'cutting_board', 'stove', 'oventray', 'toaster', 'fridge', 'coffeemaker', 'microwave', 
                        'livingroom', 'sofa', 'coffee_table', 'desk', 'cabinet', 'standing_mirror', 'globe', 
                        'mouse', 'mousemat', 'cpu_screen', 'cpu_case', 'keyboard', 'remote_control']

    new_nodes = [i for i in filter(lambda v: v["class_name"] in static_objects, graph_dict['nodes'])]
    available_id = [i["id"] for i in filter(lambda v: v["class_name"] in static_objects, graph_dict['nodes'])]

    new_edges = [i for i in filter(lambda v: v['to_id'] in available_id and v['from_id'] in available_id, graph_dict['edges'])]

    script_object2unity_object = utils.load_name_equivalence()
    unity_object2script_object = {}
    for k, vs in script_object2unity_object.items():
        unity_object2script_object[k] = k
        for v in vs:
            unity_object2script_object[v] = k

    new_nodes_script_object = []
    for node in new_nodes:
        new_nodes_script_object.append({
            "properties": node["properties"], 
            "id": node["id"], 
            "states": node["states"], 
            "category": node["category"], 
            "class_name": unity_object2script_object[node["class_name"]].lower().replace(' ', '_') if node["class_name"] in unity_object2script_object else node["class_name"].lower().replace(' ', '_')
        })
    
    json.dump({"nodes": new_nodes_script_object, "edges": new_edges}, open(path.replace('TestScene', 'TrimmedTestScene'), 'w'))
    

def add_missing_object_and_align_id(script, graph_dict, properties_data):

    possible_rooms = ['home_office', 'kitchen', 'living_room', 'bathroom', 'dining_room', 'bedroom', 'kids_bedroom', 'entrance_hall']
    available_room = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]


    objects_in_script = {}
    for script_line in script:
        for parameter in script_line.parameters:
            # room mapping
            if parameter.name == 'kitchen':
                parameter.name = 'dining_room'
            elif parameter.name == 'entrance_hall':
                parameter.name = 'living_room'
            elif parameter.name == 'home_office':
                parameter.name = 'living_room'
            elif parameter.name == 'kids_bedroom':
                parameter.name = 'bedroom'

            name = parameter.name
            if name in possible_rooms and name not in available_room:
                print("There is no {} in the environment".format(name))
                return None, False
            if (parameter.name, parameter.instance) not in objects_in_script:
                objects_in_script[(parameter.name, parameter.instance)] = parameter.instance


    #if True not in [obj[0] in available_room for obj in objects_in_script.keys()]:
    #    print("Room is not specified in this program")
    #    return None, False

    available_nodes = copy.deepcopy(graph_dict['nodes'])
    available_name = list(set([node['class_name'] for node in available_nodes]))


    id = 1000
    for obj in objects_in_script.keys():
        if obj[0] in available_name:
            # existing nodes
            for node in available_nodes:
                if node['class_name'] == obj[0]:
                    objects_in_script[obj] = node['id']
                    available_nodes.remove(node)
                    break
        else:
            # add missing nodes
            prop = properties_data[obj[0]]
                
            graph_dict['nodes'].append({
                "properties": prop, 
                "id": id, 
                "states": [], 
                "category": "placable_objects", 
                "class_name": obj[0]
            })
            objects_in_script[obj] = id
            id += 1


    # change the id in script
    for script_line in script:
        for parameter in script_line.parameters:
            if parameter.name == 'kitchen':
                parameter.name = 'dining_room'

            parameter.instance = objects_in_script[(parameter.name, parameter.instance)]
            
    return objects_in_script, True


def prepare_with_precondition(precond, objects_in_script, graph_dict):

    relation_mapping = {
        "inside": "INSIDE", 
        "location": "INSIDE", 
        "atreach": "CLOSE", 
        "in": "ON"
    }
    for p in precond:
        for k, v in p.items():
            if k in ['location', 'inside', 'atreach', 'in']:
                src_name, src_id = v[0]
                tgt_name, tgt_id = v[1]
                src_id = int(src_id)
                tgt_id = int(tgt_id)
                # room mapping
                if tgt_name.lower() == 'kitchen':
                    tgt_name = 'dining_room'
                elif tgt_name.lower() == 'entrance_hall':
                    tgt_name = 'living_room'
                elif tgt_name.lower() == 'home_office':
                    tgt_name = 'living_room'
                elif tgt_name.lower() == 'kids_bedroom':
                    tgt_name = 'bedroom'

                if k == 'location':
                    assert Room.has_value(tgt_name)

                src_id = objects_in_script[(src_name.lower().replace(' ', '_'), src_id)]
                tgt_id = objects_in_script[(tgt_name.lower().replace(' ', '_'), tgt_id)]

                graph_dict['edges'].append({'relation_type': relation_mapping[k], 'from_id': src_id, 'to_id': tgt_id})
                
            elif k in ['is_on', 'is_off', 'open']:
                _, obj_id = v
                for node in graph_dict['nodes']:
                    if node['id'] == obj_id:
                        if k == 'is_on':
                            if 'OFF' in node['states']: node['states'].remove('OFF')
                            node['states'].append('ON')
                        elif k == 'is_off':
                            if 'ON' in node['states']: node['states'].remove('ON')
                            node['states'].append('OFF')
                        elif k == 'open':
                            if 'CLOSED' in node['states']: node['states'].remove('CLOSED')
                            node['states'].append('OPEN')
                        break


def add_random_objs_graph_dict(object_placing, graph_dict, properties_data, n):

    relation_mapping = {
        "in": "INSIDE", 
        "on": "ON", 
        "nearby": "CLOSE"
    }

    objects_to_place = list(object_placing.keys())
    random.shuffle(objects_to_place)

    id = 2000
    while n > 0:

        src_name = random.choice(objects_to_place)
        tgt_names = copy.deepcopy(object_placing[src_name])
        random.shuffle(tgt_names)
        for tgt_name in tgt_names:

            tgt_nodes = [i for i in filter(lambda v: v["class_name"] == tgt_name['destination'], graph_dict["nodes"])]

            if len(tgt_nodes) > 0:
                tgt_node = tgt_nodes[0]
                tgt_id = tgt_node["id"]

                graph_dict['nodes'].append({
                    "properties": properties_data[src_name], 
                    "id": id, 
                    "states": [], 
                    "category": "placable_objects", 
                    "class_name": src_name
                })

                graph_dict["edges"].append({'relation_type': relation_mapping[tgt_name["relation"].lower()], "from_id": id, "to_id": tgt_id})
                id += 1
                n -= 1
                break


def check_2(dir_path):
    """Use precondition to modify the environment graphs
    """

    info = {}

    program_dir = os.path.join(dir_path, 'withoutconds')
    program_txt_files = glob.glob(os.path.join(program_dir, '*/*.txt'))
    properties_data = utils.load_properties_data(file_name='resources/object_script_properties_data.json')
    object_placing = json.load(open('resources/object_script_placing.json'))
    object_alias = json.load(open('resources/object_merged.json'))
    _object_alias = {}
    for k, vs in object_alias.items():
        for v in vs:
            _object_alias[v] = k
    object_alias = _object_alias


    executable_programs = 0
    not_parsable_programs = 0
    no_specified_room = 0
    for txt_file in program_txt_files:
        try:
            script = read_script(txt_file)
        except ScriptParseException:
            print("Can not parse the script: {}".format(txt_file))
            not_parsable_programs += 1            
            continue
    
        # object alias
        for script_line in script:
            for param in script_line.parameters:
                if param.name in object_alias:
                    param.name = object_alias[param.name]

        precond = read_precond(txt_file.replace('withoutconds', 'initstate').replace('txt', 'json'))

        for p in precond:
            for k, vs in p.items():
                if isinstance(vs[0], list): 
                    for v in vs:
                        v[0] = v[0].lower().replace(' ', '_')
                        if v[0] in object_alias:
                            v[0] =  object_alias[v[0]]
                else:
                    v = vs
                    v[0] = v[0].lower().replace(' ', '_')
                    if v[0] in object_alias:
                        v[0] =  object_alias[v[0]]


        # modif the graph_dict
        graph_dict = utils.load_graph_dict('example_graphs/TrimmedTestScene6_graph.json')

        objects_in_script, valid = add_missing_object_and_align_id(script, graph_dict, properties_data)        
        if not valid:
            print("Room is not specified:", txt_file)
            no_specified_room += 1
            continue

        prepare_with_precondition(precond, objects_in_script, graph_dict)
        add_random_objs_graph_dict(object_placing, graph_dict, properties_data, n=0)
        graph = EnvironmentGraph(graph_dict)

        name_equivalence = utils.load_name_equivalence()
        executor = ScriptExecutor(graph, name_equivalence)
        state = executor.execute(script)

        if state is None:
            print('Script is not executable, since {}'.format(executor.info.get_error_string()))
            info.update({txt_file: 'Script is not executable, since {}'.format(executor.info.get_error_string())})
        else:
            print('Script is executable')
            info.update({txt_file: 'Script is executable'})
            executable_programs += 1

    print("Total programs: {}, executable programs: {}".format(len(program_txt_files), executable_programs))
    print("{} programs can not be parsed".format(not_parsable_programs))
    print("{} programs do not specify the rooms or the specified room is not appear".format(no_specified_room))


def check_1(dir_path):
    """Use precondition to create the graphs
    """
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
    #check_1('/Users/andrew/UofT/instance_programs_processed_precond_nograb')
    #translate_graph_dict()
    check_2('/Users/andrew/UofT/home_sketch2program/data/programs_processed_precond_nograb')