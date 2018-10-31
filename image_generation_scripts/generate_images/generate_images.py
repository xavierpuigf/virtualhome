import sys

sys.path.append('../../virtualhome/graph_export')
from scriptcheck import UnityCommunication
from IPython import display
import json

import ipdb

comm = UnityCommunication()
print('Comm established')
#comm.reset()

x = 123


with_camera, num_cameras = comm.camera_count()
print('Num cameras', with_camera)
import scipy.misc
import os
#assert with_camera

with open('progs_in_unity.json', 'r') as f:
    programs = json.load(f)
    programs = {program: content for program, content in programs.items() if content['program_valid']}
    ipdb.set_trace()

for program in programs:
    script_name = program
    if not programs[program]['program_valid']:
        continue
    out_dir = 'sim_data/{}'.format(script_name)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    graph_name = program.replace('executable_programs', 'init_and_final_graphs').replace('.txt', '.json')
    print(graph_name)
    new_graph = json.load(open(graph_name, 'r'))['init_graph']
    comm.expand_scene(new_graph, randomize=True, random_seed=x)
    for mode in ['normal', 'seg_inst', 'seg_class', 'depth']:
        #mode = 'normal' # Possible modes are: 'normal', 'seg_inst', 'seg_class', 'depth', 'flow'
        (ok, imgs) = comm.camera_image([i for i in range(num_cameras)], mode=mode)
        status, data_list = comm.camera_data([i for i in range(num_cameras)])
        if ok:
            for it, img in enumerate(imgs):
                print(img)
                img.save('{}/{:03}_{}.png'.format(out_dir, it, mode))
                print(img)
                #display.display(img)


        with open('{}/cameras.json'.format(out_dir), 'w+') as f:
            f.write(json.dumps(data_list))
    break