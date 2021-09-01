import sys
import os
file_loc = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{file_loc}/..')
from simulation.environment import UnityEnvironment
import random

if __name__ == '__main__':
    exec_name = # your exec file here
    exec_args = {
        'file_name': exec_name
    }

    env = UnityEnvironment(num_agents=2, executable_args=exec_args)
    first_observation = env.reset()
    for agent_id in first_observation.keys():
        numobj = len(first_observation[agent_id]['nodes'])
        print(f"Agent {agent_id} sees {numobj} objects")

    rooms_ids = [(node['class_name'], node['id']) for node in first_observation[0]['nodes'] if node['category'] == 'Rooms']
    for i in range(5):
        room_name, room_id = random.choice(rooms_ids)
        random_action = f'[walk] <{room_name}> ({room_id})'
        next_obs, reward, done, info = env.step({0: random_action})
        numobj = len(next_obs[agent_id]['nodes'])
        print(f"Action: {random_action}, agent sees {numobj} objects")