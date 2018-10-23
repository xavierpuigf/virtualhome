import base64
import time
import io
import json
import requests
from PIL import Image


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

    def reset(self):
        """
        Reset scene
        """
        response = self.post_command({'id': str(time.time()), 'action': 'reset'})
        return response['success']

    def camera_count(self):
        """
        Returns the number of cameras in the scene
        """
        response = self.post_command({'id': str(time.time()), 'action': 'camera_count'})
        return response['success'], response['value']

    def camera_image(self, camera_index):
        """
        Returns the number of cameras in the scene
        """
        if not isinstance(camera_index, list):
            camera_index = [camera_index]
        response = self.post_command({'id': str(time.time()), 'action': 'camera_image', 'intParams': camera_index})
        return response['success'], _decode_image_list(response['message_list'])

    def environment_graph(self):
        """
        Returns environment graph
        """
        response = self.post_command({'id': str(time.time()), 'action': 'environment_graph'})
        return response['success'], json.loads(response['message'])

    def expand_scene(self, new_graph):
        """
        Expands scene with the given graph
        """
        response = self.post_command({'id': str(time.time()), 'action': 'expand_scene', 'stringParams':
                                      [json.dumps(new_graph)]})
        return response['success'], json.loads(response['message'])


def _decode_image(img_string):
    img_bytes = base64.b64decode(img_string)
    return Image.open(io.BytesIO(img_bytes))


def _decode_image_list(img_string_list):
    image_list = []
    for img_string in img_string_list:
        img_bytes = base64.b64decode(img_string)
        image_list.append(Image.open(io.BytesIO(img_bytes)))
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
