import time

import common
import scripts

from environment import *

class ScriptExecutor(object):

    def __init__(self, graph):
        self.graph = graph
        self.processing_time_limit = 10  # 10 seconds
        self.processing_limit = 0

    def execute(self, script):
        self.processing_limit = time.time() + self.processing_limit
        init_state = EnvironmentState(self.graph)
        return self.execute_rec(script, 0, [init_state])

    def execute_rec(self, script, script_index, state_list):
        if script_index >= len(script) or len(state_list) == 0:
            yield state_list
        future_script = script.from_index(script_index)
        current_state = state_list[-1]
        for next_state in self.call_action_method(future_script, current_state):
            next_state_list = state_list + [next_state]
            for rec_state_list in self.execute_rec(script, script_index + 1, next_state_list):
                yield rec_state_list
            if time.time() > self.processing_limit:
                break

    #
    # "Execute methods" block
    # Each function should have the following properties
    # format: execute_action(self, future_script, state, ...)
    # parameters:
    #   future_script: future script, scripts.Scrip, object, containing script lines
    #     yet to be executed, has at least one item
    #   state: current state, environment.EnvironmentState object
    # return value: enumerates possible states after execution of script_line
    #

    def execute_sit(self, future_script, state):
        pass

    def execute_goto(self, future_script, state):
        current_line = future_script[0]
        next_action = future_script[1].action if len(future_script) > 1 else None
        current_obj = current_line.object()
        # select objects based on current_obj
        for node in state.select_nodes(current_obj):
            if self.check_goto(state, node, next_action):
                yield state.move_character(node)

    def check_goto(self, state, node, next_action):
        if next_action == scripts.Action.SIT:
            state.evaluate(NodeProperty(node, Property.SITTABLE))
        else:
            return True

    def check_sittable(self, state, node):
        state.evaluate(Not(ExistsRelation(AnyNode(), Relation.ON, Node(node))))


    def execute_unknown(self, future_script, state):
        raise ExecutionException("Execution of {0} is not supported", future_script.action)

    def call_action_method(self, future_script, state):
        action_methods = {
            scripts.Action.GOTO: self.execute_goto,
            scripts.Action.SIT: self.execute_sit
        }
        method = action_methods.get(future_script, self.execute_unknown)
        return method(future_script, state)


class ExecutionException(common.Error):
    pass

