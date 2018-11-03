import base64
import collections
import time
import io
import json
import requests
from PIL import Image
import cv2
import numpy as np

class UnityCommunication(object):

    def __init__(self, url='127.0.0.1', port='8080'):
        self._address = 'http://' + url + ':' + port

    def post_command(self, request_dict):
        try:
            resp = requests.post(self._address, json=request_dict)
            if resp.status_code != requests.codes.ok:
                raise UnityEngineException(resp.status_code, resp.json())
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise UnityCommunicationException(str(e))

    def check(self, script_lines):
        """
        Returns pair (success, message); message is Null when success == True
        """
        response = self.post_command({'id': str(time.time()), 'action': 'check_script', 'stringParams': script_lines})
        return response['success'], response['message']

    def reset(self, scene_index=None):
        """
        Reset scene
        """
        response = self.post_command({'id': str(time.time()), 'action': 'reset',
                                      'intParams': [] if scene_index is None else [scene_index]})
        return response['success']

    def camera_count(self):
        """
        Returns the number of cameras in the scene
        """
        response = self.post_command({'id': str(time.time()), 'action': 'camera_count'})
        return response['success'], response['value']

    def camera_data(self, camera_indexes):
        """
        Returns camera data for cameras given in camera_indexes list
        """
        if not isinstance(camera_indexes, collections.Iterable):
            camera_indexes = [camera_indexes]
        response = self.post_command({'id': str(time.time()), 'action': 'camera_data',
                                      'intParams': camera_indexes})
        return response['success'], json.loads(response['message'])

    def camera_image(self, camera_indexes, mode='normal'):
        """
        Returns a list of renderings of cameras given in camera_indexes.
        Possible modes are: 'normal', 'seg_inst', 'seg_class', 'depth', 'flow'
        """
        if not isinstance(camera_indexes, collections.Iterable):
            camera_indexes = [camera_indexes]
        response = self.post_command({'id': str(time.time()), 'action': 'camera_image',
                                      'intParams': camera_indexes, 'stringParams': [mode]})
        return response['success'], _decode_image_list(response['message_list'])

    def environment_graph(self):
        """
        Returns environment graph
        """
        response = self.post_command({'id': str(time.time()), 'action': 'environment_graph'})
        return response['success'], json.loads(response['message'])

    def expand_scene(self, new_graph, randomize=False, random_seed=-1, prefabs_map=None):
        """
        Expands scene with the given graph.
        To use randomization set randomize to True.
        To set random seed set random_seed to a non-negative value >= 0,
        random_seed < 0 means that seed is not set
        """
        string_params = [json.dumps(new_graph)]
        int_params = [int(randomize), random_seed]
        if prefabs_map is not None:
            string_params.append(json.dumps(prefabs_map))
        response = self.post_command({'id': str(time.time()), 'action': 'expand_scene',
                                      'stringParams': string_params,
                                      'intParams': int_params})
        return response['success'], json.loads(response['message'])

    def point_cloud(self):
        response = self.post_command({'id': str(time.time()), 'action': 'point_cloud'})
        return response['success'], json.loads(response['message'])


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
