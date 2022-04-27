from .unity_environment import UnityEnvironment
from . import utils as utils_environment
import os
import json
import random

if __name__ == '__main__':
    curr_dir = os.path.dirname(os.path.realpath(__file__))

    env = UnityEnvironment(use_editor=True, num_agents=1)
    # Load dictionary with restrictions over actions

    restriction_dict_path = f'{curr_dir}/object_action_info.json'
    with open(restriction_dict_path, 'r') as f:
        restriction_dict = json.load(f)

    obs = env.reset()
    for steps in range(10):
        action_space_ids = env.get_action_space()[0]
        curr_graph = env.get_graph()
        action_str = None
        while action_str is None:
            action_name = random.choice(env.actions_available)
            object_id = random.choice(action_space_ids)
            action_str = utils_environment.can_perform_action(action_name, object_id, 0, curr_graph, restriction_dict, teleport=False)
        print(action_str)
        obs, reward, done, info = env.step({0: action_str})