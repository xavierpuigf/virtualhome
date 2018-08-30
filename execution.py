import time

import common
from environment import *
from scripts import Action
from scripts import Script


class ScriptExecutor(object):

    def __init__(self, graph: EnvironmentGraph):
        self.graph = graph
        self.processing_time_limit = 10  # 10 seconds
        self.processing_limit = 0

    def execute(self, script: Script):
        self.processing_limit = time.time() + self.processing_limit
        init_state = EnvironmentState(self.graph)
        return self.execute_rec(script, 0, init_state)

    def execute_rec(self, script: Script, script_index: int, state: EnvironmentState):
        if script_index >= len(script):
            yield state
        future_script = script.from_index(script_index)
        for next_state in self.call_action_method(future_script, state):
            for rec_state_list in self.execute_rec(script, script_index + 1, next_state):
                yield rec_state_list
            if time.time() > self.processing_limit:
                break

    #
    # "Execute methods" block
    # Each function should have the following properties
    # format: execute_action(self, future_script, state, ...)
    # parameters:
    #   future_script: future script, scripts.Script object containing script lines
    #     yet to be executed, has at least one item
    #   state: current state, environment.EnvironmentState object
    # return value: enumerates possible states after execution of script_line
    #

    def execute_sit(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_sittable(state, node):
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.ON, NodeInstance(node))],
                    node
                )
        # else: report error

    def execute_goto(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        next_action = script[1].action if len(script) > 1 else None
        current_obj = current_line.object()
        # select objects based on current_obj
        for node in state.select_nodes(current_obj):
            if self.check_goto(state, node, next_action):
                yield state.change_state(
                    [DeleteEdges(CharacterNode(), Relation.all(), AnyNode()),
                     AddEdges(CharacterNode(), Relation.INSIDE, RoomNode(node)),
                     AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(node))],
                    node,
                    current_obj
                )

    def check_goto(self, state: EnvironmentState, node: Node, next_action: Action):
        if next_action == Action.SIT:
            return state.evaluate(NodeProperty(node, Property.SITTABLE))
        else:
            return True

    def check_sittable(self, state: EnvironmentState, node: Node):
        return state.evaluate(Not(ExistsRelation(AnyNode(), Relation.ON, NodeInstance(node))))

    def execute_unknown(self, script: Script, state: EnvironmentState):
        raise ExecutionException("Execution of {0} is not supported", script[0].action)

    def call_action_method(self, script: Script, state: EnvironmentState):
        action_methods = {
            Action.GOTO: self.execute_goto,
            Action.SIT: self.execute_sit
        }
        method = action_methods.get(script[0].action, self.execute_unknown)
        return method(script, state)


class ExecutionException(common.Error):
    pass

