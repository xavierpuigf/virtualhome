

class State(object):
    pass


class ScriptExecutor(object):

    def __init__(self, environment):
        self.environment = environment

    def execute_script(self, script):
        self.execute_script_rec(self.environment.get_state(), script, 0)

    def execute_script_rec(self, state, script, script_index):
        if script_index == len(script):
            return state


