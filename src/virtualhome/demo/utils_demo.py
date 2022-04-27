import PIL
import numpy as np
import io
import os
import base64
import IPython
from sys import platform
from IPython.core.display import HTML

import sys

sys.path.append('../simulation')
from unity_simulator.comm_unity import UnityCommunication
from unity_simulator import utils_viz

comm = UnityCommunication()

def setup():
    os.chdir('../simulation/')
    if platform == 'darwin':
      os.system('open ./exec_mac.app')
    else:
      os.system('./linux_sim.x86_64')

    from unity_simulator.comm_unity import UnityCommunication
    comm = UnityCommunication()
    return comm


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

def add_cat(graph):
    graph_1 = clean_graph(graph)
    sofa = find_nodes(graph_1, class_name='sofa')[-2]
    add_node(graph_1, {'class_name': 'cat', 'category': 'Animals', 'id': 1000, 'properties': [], 'states': []})
    add_edge(graph_1, 1000, 'ON', sofa['id'])
    return graph_1

def remove_sofa(graph):
    graph_1 = clean_graph(graph)
    sofa = find_nodes(graph_1, class_name='sofa')[-2]
    graph_1['nodes'] = [x for x in graph_1['nodes'] if x['id'] != sofa['id']]
    remove_edges(graph_1, sofa)
    return graph_1

def open_fridge(graph):

    graph1 = add_beer(graph)
    graph_1 = clean_graph(graph)
    fridge = find_nodes(graph_1, class_name='fridge')[0]
    fridge['states'] = ['OPEN']
    return graph_1

def add_beer(graph):    
    graph_1 = clean_graph(graph)
    fridge = find_nodes(graph_1, class_name='fridge')[0]
    
    add_node(graph_1, {'class_name': 'beer', 'id': 1001, 'properties': [], 'states': []})
    add_edge(graph_1, 1001, 'INSIDE', fridge['id'])
    return graph_1
    
def set_tv(graph):
    tv_node = [x for x in graph['nodes'] if x['class_name'] == 'tv'][0]
    tv_node['states'] = ['ON']
    light_node = [x for x in graph['nodes'] if x['class_name'] == 'lightswitch'][0]
    light_node['states'] = ['OFF']
    return graph


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
