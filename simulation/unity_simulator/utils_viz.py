import os
import subprocess
import numpy as np

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
