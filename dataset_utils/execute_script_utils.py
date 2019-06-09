# Code to execute a script from the dataset using the python simulator
from tqdm import tqdm
import re
import glob
import sys
import os
import copy
import requests.exceptions
import json
import cv2

curr_dirname = os.path.dirname(__file__)
sys.path.append('{}/../simulation/'.format(curr_dirname))
from evolving_graph import scripts, check_programs, utils

helper = utils.graph_dict_helper()

# parses a file from the executable folder
def parse_exec_script_file(file_name):
    with open(file_name, 'r') as f:
        content = f.readlines()
        content = [x.strip() for x in content]
        title = content[0]
        description = content[1]
        script_raw = content[4:]

    script = []
    for elem in script_raw:
        script.append(re.sub('[0-9].', '', elem))

    return title, description, script

# given a file name of an environment, get an id
def obtain_scene_id_from_path(path):
    scene_name = [x for x in path.split('/') if 'TrimmedTestScene' in x][0]
    scene_number = int(scene_name.split('TrimmedTestScene')[1].split('_graph')[0])
    return scene_number

# given the message obtained from extending a scene, gets the objects that 
# could not be expanded
def obtain_objects_from_message(message):
    objects_missing = []
    for x in ['unplaced', 'missing_destinations', 'missing_prefabs']:
        if x in message.keys():
            objects_missing += message[x]
    return objects_missing

# Given a path from executable_programs, and a graph, executes the script
def render_script_from_path(comm, path_executable_file, path_graph, render_args):
    scene_id = obtain_scene_id_from_path(path_graph)
    title, description, script = parse_exec_script_file(path_executable_file)
    with open(path_graph, 'r') as f:
        content = json.load(f)
        init_graph = content['init_graph']

    result = render_script(comm, script, init_graph, scene_id-1, render_args)
    return result

# Renders a script , given a scene and initial environment
def render_script(comm, script, init_graph, scene_num, render_args):
    comm.reset(scene_num)
    if type(script) == list:
        script_content = scripts.read_script_from_list_string(script)
    else:
        script_content = scripts.read_script_from_string(script)

    script_content, _ = check_programs.modify_objects_unity2script(helper, script_content)
    success, message = comm.expand_scene(init_graph)
    
    if type(message) != dict:
        comm.reset()
        return {'success_expand': False, 
                'message': ('There was an error expanding the scene.', message)}
    else:
        objects_missing = obtain_objects_from_message(message)
        objects_script = [x[0].replace('_', '') for x in script_content.obtain_objects()]
        intersection_objects = list(set(objects_script).intersection(objects_missing))
        message_missing = 'Some objects appearing in the script were not properly initialized'
        if len(intersection_objects) > 0:
            return {'succes_expand': False, 
                    'message': (message_missing, intersection_objects)}
        else:
            render_args['skip_execution'] = render_args['image_synthesis'] is None
            success, message_exec = comm.render_script(script, **render_args)
            
            if success:
                return {'success_expand': True, 'success_exec': True}
            else:
                return {'success_expand': True, 
                        'success_exec': False, 
                        'message': (message_exec, None)}

    



