class BaseEnvironment:
    def __init__(self, env_id, num_agents):
        self.env_id = env_id
        self.num_agents = num_agents

    def reset(self):
        raise NotImplementedError

    def step(self, action_dict):
        raise NotImplementedError

    def close(self):
        pass