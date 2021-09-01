import sys
import os
file_loc = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{file_loc}/..')
import simulation
from simulation.environment import UnityEnvironment
import random
import ray
import ipdb

if __name__ == '__main__':
    ray.init()
    exec_name = # your exec file here
    exec_args = {
        'file_name': exec_name
    }
    UnityEnvironmentParallel = ray.remote(UnityEnvironment)

    num_proc = 5
    envs = []
    for i in range(num_proc):
        envs.append(UnityEnvironmentParallel.remote(num_agents=2, executable_args=exec_args, port_id=i))

    ray_obs_obj = []
    first_observations = []
    for i in range(num_proc):
        ray_obs_obj.append(envs[i].reset.remote(environment_id=(i % 3)))

    for i in range(num_proc):
        first_observations.append(ray.get(ray_obs_obj[i]))
    
    for env_id in range(num_proc):
        for agent_id in first_observations[env_id].keys():
            numobj = len(first_observations[env_id][agent_id]['nodes'])
            print(f"EnvId: {env_id} Agent {agent_id} sees {numobj} objects")

    for env in envs:
        env.close.remote()
    ipdb.set_trace()