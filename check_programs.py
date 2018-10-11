import os
import json
import utils
import glob
import copy
import random
import numpy as np
from tqdm import tqdm

from execution import Relation, State
from scripts import read_script, read_precond, ScriptParseException
from execution import ScriptExecutor
from environment import EnvironmentGraph, Room
import ipdb


random.seed(123)
verbose = True

def print_node_names(n_list):
    if len(n_list) > 0:
        print([n.class_name for n in n_list])


def write_new_txt(txt_file, precond_path, message):
    
    new_dir = 'withmessage'
    new_path = '/'.join(txt_file.split('/')[-2:])
    new_path = os.path.join(new_dir, new_path)

    new_dir = os.path.dirname(new_path)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    new_f = open(new_path, 'w')
 
    new_f.write(message)
    new_f.write('\n'*3)

    f = open(precond_path, 'r')
    f = json.load(f)
    for p in f:
        for type, objects in p.items():
            new_f.write("{}: {}".format(type, objects))
            new_f.write('\n')
    new_f.write('\n'*3)
    
    f = open(txt_file, 'r')
    new_f.write(f.read())
    f.close()

    new_f.close()


def translate_graph_dict(path):

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
        new_nodes_script_object.append({
            "properties": node["properties"], 
            "id": node["id"], 
            "states": node["states"], 
            "category": node["category"], 
            "class_name": unity_object2script_object[node["class_name"]].lower().replace(' ', '_') if node["class_name"] in unity_object2script_object else node["class_name"].lower().replace(' ', '_')
        })
    
    translated_path = path.replace('TestScene', 'TrimmedTestScene')
    json.dump({"nodes": new_nodes_script_object, "edges": new_edges, "trimmed_nodes": trimmed_nodes}, open(translated_path, 'w'))
    return translated_path


def add_missing_object_and_align_id(script, graph_dict, properties_data):

    possible_rooms = ['home_office', 'kitchen', 'living_room', 'bathroom', 'dining_room', 'bedroom', 'kids_bedroom', 'entrance_hall']
    available_rooms = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]
    available_rooms_id = [i['id'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]

    equivalent_rooms = {
        "kitchen": ["dining_room"], 
        "dining_room": ["kitchen"], 
        "entrance_hall": ["living_room"], 
        "home_office": ["living_room"], 
        "living_room": ["home_office"],
        "kids_bedroom": ["bedroom"]
    }
    room_mapping = {}
    for room in possible_rooms:
        if room not in available_rooms:
            assert room in equivalent_rooms, "Not pre-specified mapping for room: {}".format(room)
            room_mapping[room] = random.choice(equivalent_rooms[room])


    objects_in_script = {}
    room_name = None
    for script_line in script:
        for parameter in script_line.parameters:
            # room mapping
            if parameter.name in room_mapping:
                parameter.name = room_mapping[parameter.name]

            if parameter.name in available_rooms:
                room_name = parameter.name
                
            name = parameter.name
            if name in possible_rooms and name not in available_rooms:
                print("There is no {} in the environment".format(name))
                return None, False
            if (parameter.name, parameter.instance) not in objects_in_script:
                objects_in_script[(parameter.name, parameter.instance)] = parameter.instance


    available_nodes = copy.deepcopy(graph_dict['nodes'])
    available_name = list(set([node['class_name'] for node in available_nodes]))

    if room_name == None:
        # Room is not specified in this program, assign one to it
        hist = np.zeros(len(available_rooms_id))
        for obj in objects_in_script:
            obj_name = obj[0]
            for node in available_nodes:
                if node['class_name'] == obj_name:
                    edges = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] in available_rooms_id, graph_dict["edges"])]
                    
                    if len(edges) > 0:
                        for edge in edges:
                            dest_id = edge['to_id']
                            idx = available_rooms_id.index(dest_id)
                            hist[idx] += 1

        if hist.std() < 1e-5:
            # all equal
            room_name = random.choice(available_rooms)
            #print("Set a random_room")
        else:
            idx = np.argmax(hist)
            room_name = available_rooms[idx]
            #print("Pick room: {}".format(room_name))


    room_id = [i["id"] for i in filter(lambda v: v['class_name'] == room_name, graph_dict["nodes"])][0]
    id = 1000

    def _add_missing_node(_id, _obj, _category):
                
        graph_dict['nodes'].append({
            "properties": properties_data[_obj[0]], 
            "id": _id, 
            "states": [], 
            "category": _category, 
            "class_name": _obj[0]
        })
        objects_in_script[_obj] = _id
        return _id + 1

    for obj in objects_in_script.keys():
        if obj[0] in available_name:
            added = False
            # existing nodes
            for node in available_nodes:
                if node['class_name'] == obj[0]:
                    obj_in_room = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] == room_id, graph_dict["edges"])]
                    if obj[0] not in available_rooms and len(obj_in_room) == 0:
                        continue
                    else:
                        objects_in_script[obj] = node['id']
                        available_nodes.remove(node)
                        added = True
                        break
            if not added:
                # add edges
                graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": id, "to_id": room_id})
                id = _add_missing_node(id, obj, 'placing_objects')
        else:
            # add missing nodes
            graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": id, "to_id": room_id})
            id = _add_missing_node(id, obj, 'placing_objects')


    # change the id in script
    for script_line in script:
        for parameter in script_line.parameters:
            if parameter.name == 'kitchen':
                parameter.name = 'dining_room'

            parameter.instance = objects_in_script[(parameter.name, parameter.instance)]
            
    return objects_in_script, room_mapping, True


def prepare_with_precondition(precond, objects_in_script, room_mapping, graph_dict):

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
                if tgt_name.lower() in room_mapping:
                    tgt_name = room_mapping[tgt_name.lower()]

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


def check_2(dir_path, graph_path):
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
    for j, txt_file in enumerate(program_txt_files):
        
        try:
            script = read_script(txt_file)
        except ScriptParseException:
            if verbose:
                print("Can not parse the script: {}".format(txt_file))
            not_parsable_programs += 1            
            continue

        # object alias
        for script_line in script:
            for param in script_line.parameters:
                if param.name in object_alias:
                    param.name = object_alias[param.name]

        precond_path = txt_file.replace('withoutconds', 'initstate').replace('txt', 'json')
        precond = read_precond(precond_path)

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
        graph_dict = utils.load_graph_dict(graph_path)

        objects_in_script, room_mapping, valid = add_missing_object_and_align_id(script, graph_dict, properties_data) 
        utils.set_to_default_state(graph_dict)       
        if not valid:
            if verbose:
                print("Room is not specified:", txt_file)
            no_specified_room += 1
            continue

        prepare_with_precondition(precond, objects_in_script, room_mapping, graph_dict)
        add_random_objs_graph_dict(object_placing, graph_dict, properties_data, n=0)
        graph = EnvironmentGraph(graph_dict)

        name_equivalence = utils.load_name_equivalence()
        executor = ScriptExecutor(graph, name_equivalence)
        state = executor.execute(script)

        if state is None:
            message = '{}, Script is not executable, since {}'.format(j, executor.info.get_error_string())
            if verbose:
                print(message)
        else:
            message = '{}, Script is executable'.format(j)
            executable_programs += 1
            if verbose:
                print(message)

        info.update({txt_file: message})
        write_new_txt(txt_file, precond_path, message)

    print("Total programs: {}, executable programs: {}".format(len(program_txt_files), executable_programs))
    print("{} programs can not be parsed".format(not_parsable_programs))
    print("{} programs do not specify the rooms".format(no_specified_room))
    json.dump(info, open("executable_info.json", 'w'))


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
    #translated_path = translate_graph_dict(path='example_graphs/TestScene6_graph.json')
    translated_path = 'example_graphs/TrimmedTestScene6_graph.json'
    check_2('/Users/andrew/UofT/home_sketch2program/data/programs_processed_precond_nograb', graph_path=translated_path)