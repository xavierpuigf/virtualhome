
import base64
import collections
import time
import io
import json
import requests
from PIL import Image
import cv2
import numpy as np
import glob
import atexit
from sys import platform
import sys
import pdb
from . import communication

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class UnityCommunication(object):
    """
    Class to communicate with the Unity simulator and generate videos or agent behaviors

    :param str url: which url to use to communicate
    :param str port: which port to use to communicate
    :param str file_name: location of the Unity executable. If provided, it will open the executable, if `None`, it wil assume that the executable is already running
    :param str x_display: if using a headless server, display to use for rendering
    :param bool no_graphics: whether to run the simualtor without graphics
    :param bool logging: log simulator data
    :param int timeout_wait: how long to wait until connection with the simulator is called unsuccessful
    :param bool docker_enabled: whether the simulator is running in a docker container
    """

    def __init__(self, url='127.0.0.1', port='8080', file_name=None, x_display=None, no_graphics=False, logging=True,
                 timeout_wait=30, docker_enabled=False):
        self._address = 'http://' + url + ':' + port
        self.port = port
        self.graphics = no_graphics
        self.x_display = x_display
        self.launcher = None
        self.timeout_wait = timeout_wait
        if file_name is not None:
            self.launcher = communication.UnityLauncher(port=port, file_name=file_name, x_display=x_display,
                                                        no_graphics=no_graphics, logging=logging,
                                                        docker_enabled=docker_enabled)
            
            if self.launcher.batchmode:
                print('Getting connection...')
                succeeded = False
                tries = 0
                while tries < 5 and not succeeded:
                    tries += 1
                    try:
                        self.check_connection()
                        succeeded = True
                    except:
                        time.sleep(2)
                if not succeeded:
                    sys.exit()

    def requests_retry_session(
                            self,
                            retries=5,
                            backoff_factor=2,
                            status_forcelist=(500, 502, 504),
                            session=None,
                        ):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
    
        return session

    def close(self):
        if self.launcher is not None:
            self.launcher.close()


    def post_command(self, request_dict, repeat=False):
        try:
            if repeat:
                resp = self.requests_retry_session().post(self._address, json=request_dict) 
            else:
                resp = requests.post(self._address, json=request_dict, timeout=self.timeout_wait)
            if resp.status_code != requests.codes.ok:
                print(resp)
                raise UnityEngineException(resp.status_code, resp.json())
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise UnityCommunicationException(str(e))

    def check_connection(self):
        response = self.post_command(
                {'id': str(time.time()), 'action': 'idle'}, repeat=True)
        return response['success']
    
    def get_visible_objects(self, camera_index):
        """
        Obtain visible objects according to a given camera

        :param int camera_index: the camera for which you want to check the objects. Between 0 and `camera_count-1`

        :return: pair success (bool), msg: the object indices visible according to the camera

        """
        response = self.post_command({'id': str(time.time()), 'action': 'observation', 'intParams': [camera_index]})

        try:
            msg = json.loads(response['message'])
        except Exception as e:
            msg = response['message']

        return response['success'], msg

    def add_character(self, character_resource='Chars/Male1', position=None, initial_room=""):
        """
        Add a character in the scene. 

        :param str character_resource: which game object to use for the character
        # :param int char_index: the index of the character you want to move
        :param list position: the position where you want to place the character
        :param str initial_room: the room where you want to put the character, 
        if position is not specified. If this is not specified, it places character in random location

        :return: success (bool)
        """
        mode = 'random'
        pos = [0, 0, 0]
        if position is not None:
            mode = 'fix_position'
            pos = position
        elif not len(initial_room) == 0:
            assert initial_room in ["kitchen", "bedroom", "livingroom", "bathroom"]
            mode = 'fix_room'

        response = self.post_command(
            {'id': str(time.time()), 'action': 'add_character', 
             'stringParams':[json.dumps({
                'character_resource': character_resource,
                'mode': mode,
                'character_position': {'x': pos[0], 'y': pos[1], 'z': pos[2]},
                'initial_room': initial_room
                })]})
        return response['success']

    def move_character(self, char_index, pos):
        """
        Move the character `char_index` to a new position

        :param int char_index: the index of the character you want to move
        :param list pos: the position where you want to place the character

        :return: succes (bool)
        """
        response = self.post_command(
            {'id': str(time.time()),
             'action': 'move_character',
             'stringParams':[json.dumps({
                'char_index': char_index,
                'character_position': {'x': pos[0], 'y': pos[1], 'z': pos[2]},
                })]
            })
        return response['success']

    def check(self, script_lines):
        response = self.post_command({'id': str(time.time()), 'action': 'check_script', 'stringParams': script_lines})
        return response['success'], response['message']

    def add_camera(self, position=[0,1,0], rotation=[0,0,0], field_view=40):
        """
        Add a new scene camera. The camera will be static in the scene.

        :param list position: the position of the camera, with respect to the agent
        :param list rotation: the rotation of the camera, with respect to the agent
        :param list field_view: the field of view of the camera

        :return: succes (bool)
        """
        cam_dict = {
                'position': {'x': position[0], 'y': position[1], 'z': position[2]},
                'rotation': {'x': rotation[0], 'y': rotation[1], 'z': rotation[2]},
                'field_view': field_view
        }
        response = self.post_command(
                {'id': str(time.time()), 'action': 'add_camera',
                    'stringParams': [json.dumps(cam_dict)]})
        return response['success'], response['message']

    def update_camera(self, camera_index, position=[0,1,0], rotation=[0,0,0], field_view=40):
        """
        Updates an existing camera, identified by index.
        :param int camera_index: the index of the camera you want to update
        :param list position: the position of the camera, with respect to the agent
        :param list rotation: the rotation of the camera, with respect to the agent
        :param list field_view: the field of view of the camera

        :return: succes (bool)
        """
        cam_dict = {

                'position': {'x': position[0], 'y': position[1], 'z': position[2]},
                'rotation': {'x': rotation[0], 'y': rotation[1], 'z': rotation[2]},
                'field_view': field_view
        }
        response = self.post_command(
                {'id': str(time.time()), 'action': 'update_camera',
                    'intParams': [camera_index],
                    'stringParams': [json.dumps(cam_dict)]})
        return response['success'], response['message']


    def add_character_camera(self, position=[0,1,0], rotation=[0,0,0], field_view=60, name="new_camera"):
        """
        Add a new character camera. The camera will be added to every character you include in the scene, and it will move with 
        the character. This must be called before adding any character.

        :param list position: the position of the camera, with respect to the agent
        :param list rotation: the rotation of the camera, with respect to the agent
        :name: the name of the camera, used for recording when calling render script

        :return: succes (bool)
        """
        cam_dict = {
                'position': {'x': position[0], 'y': position[1], 'z': position[2]},
                'rotation': {'x': rotation[0], 'y': rotation[1], 'z': rotation[2]},
                'field_view': field_view,
                'camera_name': name
        }
        response = self.post_command(
                {'id': str(time.time()), 'action': 'add_character_camera',
                    'stringParams': [json.dumps(cam_dict)]})
        return response['success'], response['message']

    def update_character_camera(self, position=[0,1,0], rotation=[0,0,0], field_view=60, name="PERSON_FRONT"):
        """
        Update character camera specified by name. This must be called before adding any character.

        :param list position: the position of the camera, with respect to the agent
        :param list rotation: the rotation of the camera, with respect to the agent
        :name: the name of the camera, used for recording when calling render script

        :return: succes (bool)
        """
        cam_dict = {
                'position': {'x': position[0], 'y': position[1], 'z': position[2]},
                'rotation': {'x': rotation[0], 'y': rotation[1], 'z': rotation[2]},
                'field_view': field_view,
                'camera_name': name
        }
        response = self.post_command(
                {'id': str(time.time()), 'action': 'update_character_camera',
                    'stringParams': [json.dumps(cam_dict)]})
        return response['success'], response['message']

    def reset(self, environment=None):
        """
        Reset scene. Deletes characters and scene changes, and loads the scene in scene_index

        :param int environment: integer between 0 and 49, corresponding to the apartment we want to load
        :return: succes (bool)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'clear',
                                  'intParams': [] if environment is None else [environment]})
        response = self.post_command({'id': str(time.time()), 'action': 'environment',
                                    'intParams': [] if environment is None else [environment]})
        return response['success']

    def fast_reset(self, environment=None):
        """
        Fast scene. Deletes characters and scene changes

        :return: success (bool)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'fast_reset',
                                  'intParams': [] if environment is None else [environment]})
        return response['success']

    def procedural_generation(self, seed=None):
        """
        Generates new environments through procedural generation logic.

        :param int seed: integer corresponding to the seed given during generation
        :return: success (bool), seed: (integer)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'clear_procedural',
                                      'intParams': []})
        response = self.post_command({'id': str(time.time()), 'action': 'procedural_generation',
                                  'intParams': [] if seed is None else [seed]})
        return response['success'], response['message']

    def camera_count(self):
        """
        Returns the number of cameras in the scene, including static cameras, and cameras for each character

        :return: pair success (bool), num_cameras (int)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'camera_count'})
        return response['success'], response['value']

    def character_cameras(self):
        """
        Returns the number of cameras in the scene

        :return: pair success (bool), camera_names: (list): the names of the cameras defined fo the characters
        """
        response = self.post_command({'id': str(time.time()), 'action': 'character_cameras'})
        return response['success'], response['message']

    def camera_data(self, camera_indexes):
        """
        Returns camera data for cameras given in camera_indexes list

        :param list camera_indexes: the list of cameras to return, can go from 0 to `camera_count-1`
        :return: pair success (bool), cam_data: (list): for every camera, the matrices with the camera parameters
        """
        if not isinstance(camera_indexes, collections.Iterable):
            camera_indexes = [camera_indexes]
        response = self.post_command({'id': str(time.time()), 'action': 'camera_data',
                                      'intParams': camera_indexes})
        return response['success'], json.loads(response['message'])

    def camera_image(self, camera_indexes, mode='normal', image_width=640, image_height=480):
        """
        Returns a list of renderings of cameras given in camera_indexes.

        :param list camera_indexes: the list of cameras to return, can go from 0 to `camera_count-1`
        :param str mode: what kind of camera rendering to return. Possible modes are: "normal", "seg_inst", "seg_class", "depth", "flow", "albedo", "illumination", "surf_normals"
        :param int image_width: width of the returned images
        :param int image_height: height of the returned iamges

        :return: pair success (bool), images: (list) a list of images according to the camera rendering mode
        """
        if not isinstance(camera_indexes, collections.Iterable):
            camera_indexes = [camera_indexes]

        params = {'mode': mode, 'image_width': image_width, 'image_height': image_height}
        response = self.post_command({'id': str(time.time()), 'action': 'camera_image',
                                      'intParams': camera_indexes, 'stringParams': [json.dumps(params)]})
        return response['success'], _decode_image_list(response['message_list'])

    def instance_colors(self):
        """
        Return a mapping from rgb colors, shown on `seg_inst` to object `id`, specified in the environment graph.

        :return: pair success (bool), mapping: (dictionary)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'instance_colors'})
        return response['success'], json.loads(response['message'])

    def environment_graph(self):
        """
        Returns environment graph, at the current state

        :return: pair success (bool), graph: (dictionary)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'environment_graph'})
        return response['success'], json.loads(response['message'])

    def expand_scene(self, new_graph, randomize=False, random_seed=-1, animate_character=False,
                     ignore_placing_obstacles=False, prefabs_map=None, transfer_transform=True):
        """
        Expands scene with the given graph. Given a starting scene without characters, it updates the scene according to new_graph, which contains a modified description of the scene. Can be used to add, move, or remove objects or change their state or size.

        :param dict new_graph: a dictionary corresponding to the new graph of the form `{'nodes': ..., 'edges': ...}`
        :param int bool randomize: a boolean indicating if the new positioni/types of objects should be random
        :param int random_seed: seed to use for randomize. random_seed < 0 means that seed is not set
        :param bool animate_character: boolean indicating if the added character should be frozen or not.
        :param bool ignore_placing_obstacles: when adding new objects, if the transform is not specified, whether to consider if it collides with existing objects
        :param dict prefabs_map: dictionary to specify which Unity game objects should be used when creating new objects
        :param bool transfer_transform: boolean indicating if we should set the exact position of new added objects or not

        :return: pair success (bool), message: (str)
        """
        config = {
            'randomize': randomize, 
            'random_seed': random_seed, 
            'animate_character': animate_character,
            'ignore_obstacles': ignore_placing_obstacles, 
            'transfer_transform': transfer_transform
        }
        string_params = [json.dumps(config), json.dumps(new_graph)]
        int_params = [int(randomize), random_seed]

        if prefabs_map is not None:
            string_params.append(json.dumps(prefabs_map))
        response = self.post_command({'id': str(time.time()), 'action': 'expand_scene',
                                      'stringParams': string_params})
        try:
            message = json.loads(response['message'])
        except ValueError:
            message = response['message']
        return response['success'], message

    def set_time(self, hours=0, minutes=0, seconds=0):
        """
        Set the time in the environment

        :param int hours: hours in 24-hour time
        :param int minutes: minutes in 24-hour time
        :param int seconds: seconds in 24-hour time
        :param int scaler: scaler is a multipler that increase/decreases time step

        :return: success (bool)
        """
        time_dict = {
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds
        }
        response = self.post_command(
                {'id': str(time.time()), 'action': 'set_time',
                    'stringParams': [json.dumps(time_dict)]})
        return response['success']

    def activate_physics(self, gravity=-10):
        """
        Activates gravity and realistic collisions in the environment

        :param list gravity: int of gravity value experienced in the environment

        :return: success (bool)
        """
        physics_dict = {
                'gravity': gravity
        }
        response = self.post_command(
                {'id': str(time.time()), 'action': 'activate_physics',
                    'stringParams': [json.dumps(physics_dict)]})
        return response['success']

    def remove_terrain(self):
        """
        remove_terrain. Deletes terrain

        :return: success (bool)
        """
        response = self.post_command({'id': str(time.time()), 'action': 'remove_terrain',
                                      'intParams': []})
        return response['success']

    def point_cloud(self):
        response = self.post_command({'id': str(time.time()), 'action': 'point_cloud'})
        return response['success'], json.loads(response['message'])

    def render_script(self, script, randomize_execution=False, random_seed=-1, processing_time_limit=10,
                      skip_execution=False, find_solution=False, output_folder='Output/', file_name_prefix="script",
                      frame_rate=5, image_synthesis=['normal'], save_pose_data=False,
                      image_width=640, image_height=480, recording=False,
                      save_scene_states=False, camera_mode=['AUTO'], time_scale=1.0, skip_animation=False):
        """
        Executes a script in the simulator. The script can be single or multi agent, 
        and can be used to generate a video, or just to change the state of the environment

        :param list script: a list of script lines, of the form `['<char{id}> [{Action}] <{object_name}> ({object_id})']`
        :param bool randomize_execution: randomly choose elements
        :param int random_seed: random seed to use when randomizing execution, -1 means that the seed is not set
        :param bool find_solution: find solution (True) or use graph ids to determine object instances (False)
        :param int processing_time_limit: time limit for finding a solution in seconds
        :param int skip_execution: skip rendering, only check if a solution exists
        :param str output_folder: folder to output renderings
        :param str file_name_prefix: prefix of created files
        :param int frame_rate: frame rate at which to generate the video
        :param list image_synthesis: what information to save. Can be multiple at the same time. Modes are: "normal", "seg_inst", "seg_class", "depth", "flow", "albedo", "illumination", "surf_normals". Leave empty if you don't want to generate anythign
        :param bool save_pose_data: save pose data, a skeleton for every agent and frame
        :param int image_width: image_height for the generated frames
        :param int image_height: image_height for the generated frames
        :param bool recording: whether to record data with cameras
        :param bool save_scene_states: save scene states (this will be unused soon)
        :param list camera_mode: list with cameras used to render data. Can be a str(i) with i being a scene camera index or one of the cameras from `character_cameras`
        :param int time_scale: accelerate time at which actions happen
        :param bool skip_animation: whether agent should teleport/do actions without animation (True), or perform the animations (False) 

        :return: pair success (bool), message: (str)
        """
        params = {'randomize_execution': randomize_execution, 'random_seed': random_seed,
                  'processing_time_limit': processing_time_limit, 'skip_execution': skip_execution,
                  'output_folder': output_folder, 'file_name_prefix': file_name_prefix,
                  'frame_rate': frame_rate, 'image_synthesis': image_synthesis, 
                  'find_solution': find_solution,
                  'save_pose_data': save_pose_data, 'save_scene_states': save_scene_states,
                  'camera_mode': camera_mode, 'recording': recording,
                  'image_width': image_width, 'image_height': image_height,
                  'time_scale': time_scale, 'skip_animation': skip_animation}
        response = self.post_command({'id': str(time.time()), 'action': 'render_script',
                                      'stringParams': [json.dumps(params)] + script})

        try:
            message = json.loads(response['message'])
        except ValueError:
            message = response['message']
        
        return response['success'], message

        
def _decode_image(img_string):
    img_bytes = base64.b64decode(img_string)
    if 'PNG' == img_bytes[1:4]:
        img_file = cv2.imdecode(np.fromstring(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    else:
        img_file = cv2.imdecode(np.fromstring(img_bytes, np.uint8), cv2.IMREAD_ANYDEPTH+cv2.IMREAD_ANYCOLOR)
    return img_file


def _decode_image_list(img_string_list):
    image_list = []
    for img_string in img_string_list:
        image_list.append(_decode_image(img_string))
    return image_list


class UnityEngineException(Exception):
    """
    This exception is raised when an error in communication occurs:
    - Unity has received invalid request
    More information is in the message.
    """
    def __init__(self, status_code, resp_dict):
        resp_msg = resp_dict['message'] if 'message' in resp_dict else 'Message not available'
        self.message = 'Unity returned response with status: {0} ({1}), message: {2}'.format(
            status_code, requests.status_codes._codes[status_code][0], resp_msg)


class UnityCommunicationException(Exception):
    def __init__(self, message):
        self.message = message
