import os
import subprocess
import numpy as np

import PIL
import numpy as np
import io
import os
import base64
import IPython
from sys import platform
from IPython.core.display import HTML

import sys

from unity_simulator.comm_unity import UnityCommunication
from unity_simulator import utils_viz


def setup():
    os.chdir('../simulation/')
    if platform == 'darwin':
      os.system('open ./exec_mac.app')
    else:
      os.system('./linux_sim.x86_64')

    from unity_simulator.comm_unity import UnityCommunication
    comm = UnityCommunication()
    return comm


def generate_video(input_path, prefix, char_id=0, image_synthesis=['normal'], frame_rate=5, output_path=None):
    """ Generate a video of an episode """
    if output_path is None:
        output_path = input_path

    vid_folder = '{}/{}/{}/'.format(input_path, prefix, char_id)
    if not os.path.isdir(vid_folder):
        print("The input path: {} you specified does not exist.".format(input_path))
    else:
        for vid_mod in image_synthesis:
            command_set = ['ffmpeg', '-i',
                             '{}/Action_%04d_0_{}.png'.format(vid_folder, vid_mod), 
                             '-framerate', str(frame_rate),
                             '-pix_fmt', 'yuv420p',
                             '{}/video_{}.mp4'.format(output_path, vid_mod)]
            subprocess.call(command_set)
            print("Video generated at ", '{}/video_{}.mp4'.format(output_path, vid_mod))

def read_pose_file(file_name, prefix):
    with open('{}/pd_{}.txt'.format(file_name, prefix), 'r') as f:
        content = f.readlines()[1:]

    pose = []
    for l in content:
        pose.append(np.array([float(x) for x in l.split(' ')]))
    return pose

def get_skeleton(input_path, prefix, char_id=0):
    skeleton_file = '{}/{}/{}/'.format(input_path, prefix, char_id)
    skeleton_content = read_pose_file(skeleton_file, prefix)
    pose_char = np.array(skeleton_content)[:, 1:]
    frame_index = np.array(skeleton_content)[:, 1:]
    pose_char = pose_char.reshape((pose_char.shape[0], -1, 3))
    valid_pose = pose_char.sum(-1).sum(0) != 0
    return pose_char[:, valid_pose, :], frame_index

def world2im(camera_data, wcoords, imw, imh):
    """ Go from 3D to pixel coords 
    - camera_data: camera info, comes from comm.camera_data()[1][0]
    - wcoords: array of Nx3 of 3D points in the environment

    usage:
    cam_id = 32
    imw, img = 800, 400
    s, graph = comm.environment_graph()
    s, im = comm.camera_image([cid], image_width=imw, image_height=imh)
    s, cd = comm.camera_data([cid])
    wcoord = np.array([node['bounding_box']['center'] for node in graph['nodes'] if node['class_name'] in ['tv', 'pillow']])
    pos = utils_viz.world2im(cd[0], np.array(wcoord), imw, img)
    for i in range(pos.shape[1]):
        cv2.drawMarker(im[0], tuple(pos[:, i].astype(np.int32)), (0,255,255), markerSize=20, thickness=2)
    """
    wcoords = wcoords.transpose()
    if len(wcoords.shape) < 2:
        return None
    naspect = float(imw/imh)
    aspect = camera_data['aspect']
    proj = np.array(camera_data['projection_matrix']).reshape((4,4)).transpose()
    w2cam = np.array(camera_data['world_to_camera_matrix']).reshape((4,4)).transpose()
    cw = np.concatenate([wcoords, np.ones((1, wcoords.shape[1]))], 0) # 4 x N
    pixelcoords = np.matmul(proj, np.matmul(w2cam, cw)) # 4 x N
    pixelcoords = pixelcoords/pixelcoords[-1, :]
    pixelcoords[0, :] *= (aspect/naspect)
    pixelcoords = (pixelcoords + 1)/2.
    pixelcoords[1,:] = 1. - pixelcoords[1, :]
    pixelcoords = pixelcoords[:2, :] * np.array([imw, imh])[:, None]
    return pixelcoords[:2, :]


### Utils nodes
def find_nodes(graph, **kwargs):
    if len(kwargs) == 0:
        return None
    else:
        k, v = next(iter(kwargs.items()))
        return [n for n in graph['nodes'] if n[k] == v]
    
def find_edges_from(graph, id):
    nb_list = [(e['relation_type'], e['to_id']) for e in graph['edges'] if e['from_id'] == id]
    return [(rel, find_nodes(graph, id=n_id)[0]) for (rel, n_id) in nb_list]

def clean_graph(graph):
    new_nodes = []
    for n in graph['nodes']:
        nc = dict(n)
        if 'bounding_box' in nc:
            del nc['bounding_box']
        new_nodes.append(nc)
    return {'nodes': new_nodes, 'edges': list(graph['edges'])}

def remove_edges(graph, n, fr=True, to=True):
    n_id = n['id']
    new_edges = [e for e in graph['edges'] if 
                 (e['from_id'] != n_id or not fr) and (e['to_id'] != n_id or not to)]
    graph['edges'] = new_edges

def remove_edge(graph, fr_id, rel, to_id):
    new_edges = [e for e in graph['edges'] if 
                 not (e['from_id'] == fr_id and e['to_id'] == to_id and e['relation_type'] == rel)]
    graph['edges'] = new_edges
    
def add_node(graph, n):
    graph['nodes'].append(n)

def add_edge(graph, fr_id, rel, to_id):
    graph['edges'].append({'from_id': fr_id, 'relation_type': rel, 'to_id': to_id})
    
def clean_graph(graph):
    new_nodes = []
    for n in graph['nodes']:
        nc = dict(n)
        if 'bounding_box' in nc:
            del nc['bounding_box']
        new_nodes.append(nc)
    return {'nodes': new_nodes, 'edges': list(graph['edges'])}


### utils_images
def display_grid_img(images_old, nrows=1):
    images = [x for x in images_old]
    h, w, _ = images[0].shape
    ncols = int((len(images)+nrows-1)/nrows)
    missing = ncols - (len(images)%ncols)
    for m in range(missing):
        images.append(np.zeros((h, w, 3)).astype(np.uint8))
    img_final = []
    for it_r in range(nrows):
        init_ind = it_r * ncols 
        end_ind = init_ind + ncols
        images_take = [images[it] for it in range(init_ind, end_ind)]
        img_final.append(np.concatenate(images_take, 1))
    img_final = np.concatenate(img_final, 0)
    img_final = PIL.Image.fromarray(img_final[:,:,::-1])
    return img_final

def get_scene_cameras(comm, ids, mode='normal'):
    _, ncameras = comm.camera_count()
    cameras_select = list(range(ncameras))
    cameras_select = [cameras_select[x] for x in ids]
    (ok_img, imgs) = comm.camera_image(cameras_select, mode=mode, image_width=640, image_height=360)
    return imgs

def display_scene_cameras(comm, ids, nrows=1, mode='normal'):
    imgs = get_scene_cameras(comm, ids, mode)
    return display_grid_img(imgs, nrows=nrows)

def display_scene_modalities(
    comm, ids, modalities=['normal', 'seg_class', 'seg_inst', 'depth'], nrows=1):
    _, ncameras = comm.camera_count()
    cameras_select = list(range(ncameras))
    cameras_select = [cameras_select[x] for x in ids]
    imgs_modality = []
    for mode_name in modalities:
        (ok_img, imgs) = comm.camera_image(cameras_select, mode=mode_name, image_width=640, image_height=320)
        if mode_name == 'depth':
            imgs = [(x*255./np.max(x)).astype(np.uint8) for x in imgs]

        imgs_modality += imgs
    img_final = display_grid_img(imgs_modality, nrows=nrows)
    return img_final


## Utils video
def run_program(comm, prog, name):
    comm.render_script(prog, processing_time_limit=60, find_solution=True, file_name_prefix=name)
    out_file = './Output/{}/Action_normal.mp4'.format(name)
    return out_file

def display_vid(vid_path):
    video = io.open(vid_path, 'r+b').read()
    encoded = base64.b64encode(video)
    return HTML(data='''<video alt="test" controls>
    <source src="data:video/mp4;base64,{0}" type="video/mp4" /> </video>'''.format(encoded.decode('ascii')))
