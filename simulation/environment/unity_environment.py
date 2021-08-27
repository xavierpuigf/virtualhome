from .base_environment import BaseEnvironment
import sys
import os

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{curr_dir}/../')

from unity_simulator import comm_unity as comm_unity
from . import utils as utils_environment
from evolving_graph import utils
import atexit
import random
import pdb
import ipdb
import random
import json
import numpy as np

class UnityEnvironment(BaseEnvironment):


    def __init__(self,
                 num_agents=2,
                 max_episode_length=200,
                 observation_types=None,
                 use_editor=False,
                 base_port=8080,
                 port_id=0,
                 executable_args={},
                 recording_options={'recording': False, 
                                    'output_folder': None, 
                                    'file_name_prefix': None,
                                    'cameras': 'PERSON_FROM_BACK',
                                    'modality': 'normal'},
                 seed=123):


        self.seed = seed
        self.prev_reward = 0.
        self.rnd = random.Random(seed)
        np.random.seed(seed)


        self.steps = 0
        self.env_id = None
        self.max_ids = {}


        self.num_agents = num_agents
        self.max_episode_length = max_episode_length
        self.actions_available = [
            'turnleft',
            'walkforward',
            'turnright',
            'walktowards',
            'open',
            'close',
            'put',
            'grab',
            'no_action'
        ]

        self.recording_options = recording_options
        self.base_port = base_port
        self.port_id = port_id
        self.executable_args = executable_args

        # Observation parameters
        self.num_camera_per_agent = 6
        self.CAMERA_NUM = 1  # 0 TOP, 1 FRONT, 2 LEFT..
        self.default_image_width = 300
        self.default_image_height = 300

        if observation_types is not None:
            self.observation_types = observation_types
        else:
            self.observation_types = ['partial' for _ in range(num_agents)]

        
        self.agent_info = {
            0: 'Chars/Female1',
            1: 'Chars/Male1'
        }
        

        self.changed_graph = True
        self.rooms = None
        self.id2node = None
        self.num_static_cameras = None


        if use_editor:
            # Use Unity Editor
            self.port_number = 8080
            self.comm = comm_unity.UnityCommunication()
        else:
            # Launch the executable
            self.port_number = self.base_port + port_id
            # ipdb.set_trace()
            self.comm = comm_unity.UnityCommunication(port=str(self.port_number), **self.executable_args)

        atexit.register(self.close)
        self.reset()




    def close(self):
        self.comm.close()

    def relaunch(self):
        self.comm.close()
        self.comm = comm_unity.UnityCommunication(port=str(self.port_number), **self.executable_args)

    def reward(self):
        # Define here your reward
        reward = 0
        done = False
        info = {}
        return reward, done, info

    def step(self, action_dict):
        script_list = utils_environment.convert_action(action_dict)
        if len(script_list[0]) > 0:
            if self.recording_options['recording']:
                success, message = self.comm.render_script(script_list,
                                                           recording=True,
                                                           skip_animation=False,
                                                           camera_mode=self.recording_options['cameras'],
                                                           file_name_prefix='task_{}'.format(self.task_id),
                                                           image_synthesis=self.recording_optios['modality'])
            else:
                success, message = self.comm.render_script(script_list,
                                                           recording=False,
                                                           skip_animation=True)
            if not success:
                print(message)
            else:
                self.changed_graph = True

        # Obtain reward
        reward, done, info = self.reward()

        graph = self.get_graph()
        self.steps += 1
        
        obs = self.get_observations()
        

        info['finished'] = done
        info['graph'] = graph
        if self.steps == self.max_episode_length:
            done = True
        return obs, reward, done, info

    def reset(self, environment_graph=None, environment_id=None, init_rooms=None):
        """
        :param environment_graph: the initial graph we should reset the environment with
        :param environment_id: which id to start
        :param init_rooms: where to intialize the agents
        """
        self.env_id = environment_id
        print("Resetting env", self.env_id)

        if self.env_id is not None:
            self.comm.reset(self.env_id)
        else:
            self.comm.reset()

        s,g = self.comm.environment_graph()
        if self.env_id not in self.max_ids.keys():
            max_id = max([node['id'] for node in g['nodes']])
            self.max_ids[self.env_id] = max_id

        max_id = self.max_ids[self.env_id]
        #print(max_id)
        if environment_graph is not None:
            # TODO: this should be modified to extend well
            # updated_graph = utils.separate_new_ids_graph(environment_graph, max_id)
            updated_graph = environment_graph
            success, m = self.comm.expand_scene(updated_graph)
        else:
            success = True

        if not success:
            print("Error expanding scene")
            pdb.set_trace()
            return None
        self.num_static_cameras = self.comm.camera_count()[1]

        if init_rooms is None or init_rooms[0] not in ['kitchen', 'bedroom', 'livingroom', 'bathroom']:
            rooms = self.rnd.sample(['kitchen', 'bedroom', 'livingroom', 'bathroom'], 2)
        else:
            rooms = list(init_rooms)

        for i in range(self.num_agents):
            if i in self.agent_info:
                self.comm.add_character(self.agent_info[i], initial_room=rooms[i])
            else:
                self.comm.add_character()

        _, self.init_unity_graph = self.comm.environment_graph()


        self.changed_graph = True
        graph = self.get_graph()
        self.rooms = [(node['class_name'], node['id']) for node in graph['nodes'] if node['category'] == 'Rooms']
        self.id2node = {node['id']: node for node in graph['nodes']}

        obs = self.get_observations()
        self.steps = 0
        self.prev_reward = 0.
        return obs

    def get_graph(self):
        if self.changed_graph:
            s, graph = self.comm.environment_graph()
            if not s:
                pdb.set_trace()
            self.graph = graph
            self.changed_graph = False
        return self.graph

    def get_observations(self):
        dict_observations = {}
        for agent_id in range(self.num_agents):
            obs_type = self.observation_types[agent_id]
            dict_observations[agent_id] = self.get_observation(agent_id, obs_type)
        return dict_observations

    def get_action_space(self):
        dict_action_space = {}
        for agent_id in range(self.num_agents):
            if self.observation_types[agent_id] not in ['partial', 'full']:
                raise NotImplementedError
            else:
                # Even if you can see all the graph, you can only interact with visible objects
                obs_type = 'partial'
            visible_graph = self.get_observation(agent_id, obs_type)
            dict_action_space[agent_id] = [node['id'] for node in visible_graph['nodes']]
        return dict_action_space

    def get_observation(self, agent_id, obs_type, info={}):
        if obs_type == 'partial':
            # agent 0 has id (0 + 1)
            curr_graph = self.get_graph()
            return utils.get_visible_nodes(curr_graph, agent_id=(agent_id+1))

        elif obs_type == 'full':
            return self.get_graph()

        elif obs_type == 'visible':
            # Only objects in the field of view of the agent
            raise NotImplementedError

        elif obs_type == 'image':
            camera_ids = [self.num_static_cameras + agent_id * self.num_camera_per_agent + self.CAMERA_NUM]
            if 'image_width' in info:
                image_width = info['image_width']
                image_height = info['image_height']
            else:
                image_width, image_height = self.default_image_width, self.default_image_height
            if 'mode' in info:
                current_mode = info['mode']
            else:
                current_mode = 'normal'
            s, images = self.comm.camera_image(camera_ids, mode=current_mode, image_width=image_width, image_height=image_height)
            if not s:
                pdb.set_trace()
            return images[0]
        else:
            raise NotImplementedError


        
