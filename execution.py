import time

import common
from environment import *
from scripts import Action
from scripts import Script


# ActionExecutor-s
###############################################################################


class ActionExecutor(object):

    @abstractmethod
    def execute(self, script: Script, state: EnvironmentState):
        """
        :param script: future script, scripts.Script object containing script lines
            yet to be executed, has at least one item
        :param state: current state, environment.EnvironmentState object
        :return: enumerates possible states after execution of script_line
        """
        pass


class UnknownExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        raise ExecutionException("Execution of {0} is not supported", script[0].action)


class SitExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_sittable(state, node):
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.ON, NodeInstance(node))],
                    node
                )

    def check_sittable(self, state: EnvironmentState, node: Node):
        tm = TimeMeasurement.start('check_sittable')
        result = state.evaluate(Not(ExistsRelation(AnyNode(), Relation.ON, NodeInstanceFilter(node))))
        TimeMeasurement.stop(tm)
        return result


class GotoExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
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

    def check_goto(self, state: EnvironmentState, node: GraphNode, next_action: Action):
        char = get_character_node(state)
        if next_action == Action.SIT:
            return Property.SITTABLE in node.properties
        else:
            return True


class GrabExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_grabbable(state, node):
                yield state.change_state([], node)

    def check_grabbable(self, state: EnvironmentState, node: GraphNode):
        return state.evaluate(
            And(Constant(Property.GRABBABLE in node.properties),
                ExistsRelation(CharacterNode(), Relation.CLOSE, NodeInstanceFilter(node)),
                Not(ExistsRelation(NodeInstance(node), Relation.INSIDE,
                                   NodeConditionFilter(And(
                                       NodeAttrIn('states', State.OPEN),
                                       Not(IsRoomNode())))))
            )
        )


# ScriptExecutor
###############################################################################


class ScriptExecutor(object):

    _action_executors = {
        Action.GOTO: GotoExecutor(),
        Action.SIT: SitExecutor(),
        Action.GRAB: GrabExecutor()
    }

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

    def call_action_method(self, script: Script, state: EnvironmentState):
        executor = ScriptExecutor._action_executors.get(script[0].action, UnknownExecutor())
        return executor.execute(script, state)


class ExecutionException(common.Error):
    pass


# Helpers
###############################################################################


def get_character_node(state: EnvironmentState):
    chars = state.get_nodes_by_attr('class_name', 'character')
    return None if len(chars) == 0 else chars[0]