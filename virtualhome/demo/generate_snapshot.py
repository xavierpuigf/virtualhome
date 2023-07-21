# Generate snapshot for a program. Make sure you have the executable open
import json
import sys
import numpy as np
import random
import cv2

sys.path.append('../simulation')
sys.path.append('../dataset_utils')

from tqdm import tqdm
from unity_simulator.comm_unity import UnityCommunication
import add_preconds
import evolving_graph.check_programs as check_programs

# Add here your script
script = ['[Walk] <television> (1)', '[SwitchOn] <television> (1)', 
          '[Walk] <sofa> (1)', '[Find] <controller> (1)',
          '[Grab] <controller> (1)']


cameras_ids = [-6, -5, -1]

def build_grid_images(images):
    image_steps = []
    for image_step in images:
        img_step_cameras = np.concatenate(image_step, 1)
        image_steps.append(img_step_cameras)
    final_image = np.concatenate(image_steps, 0)
    return final_image

def obtain_snapshots(graph_state_list, reference_graph, comm):
    _, ncameras = comm.camera_count()
    cameras_select = list(range(ncameras))
    cameras_select = [cameras_select[x] for x in cameras_ids]
    
    seed = random.randint(1,100)
    messages_expand, images = [], []
    for graph_state in tqdm(graph_state_list):
        comm.reset(0)
        comm.add_character()

        message = comm.expand_scene(graph_state, randomize=True, random_seed=seed)
        messages_expand.append(message)
        print(message)
        _ = comm.camera_image(cameras_select, mode='normal', image_height=480,  image_width=640)
        ok, imgs = comm.camera_image(cameras_select, mode='normal', image_height=480,  image_width=640)
        images.append(imgs)

    return messages_expand, images


comm = UnityCommunication()

print('Inferring preconditions...')
preconds = add_preconds.get_preconds_script(script).printCondsJSON()
print(preconds)

print('Loading graph')
comm.reset(0)
comm.add_character()
_, graph_input = comm.environment_graph()
print('Executing script')
print(script)
graph_input = check_programs.translate_graph_dict_nofile(graph_input)
info = check_programs.check_script(
        script, preconds, graph_path=None, inp_graph_dict=graph_input)

message, final_state, graph_state_list, graph_dict, id_mapping, info, helper, modif_script = info
success = (message == 'Script is executable')

if success:
    print('Generating snapshots')
    messages, images = obtain_snapshots(graph_state_list, graph_input, comm)
    grid_img = build_grid_images(images)
    cv2.imwrite('snapshot_test.png', grid_img)
    print('Snapshot saved in demo/snapshot_test.png')
    
