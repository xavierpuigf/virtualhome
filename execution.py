import time
from typing import Optional

import common
from environment import *
from preparation import StatePrepare
from scripts import Action, Script


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
                char_node = _get_character_node(state)
                new_char_node = char_node.copy()
                new_char_node.states.add(State.SITTING)
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.ON, NodeInstance(node)),
                     ChangeNode(new_char_node)]
                )

    def check_sittable(self, state: EnvironmentState, node: GraphNode):
        if not _is_character_close_to(state, node):
            return False
        char_node = _get_character_node(state)
        if State.SITTING in char_node.states:
            return False
        if Property.SITTABLE not in node.properties:
            return False
        return not state.evaluate(ExistsRelation(AnyNode(), Relation.ON, NodeInstanceFilter(node)))


class StandUpExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        char_node = _get_character_node(state)
        if State.SITTING in char_node.states:
            new_char_node = char_node.copy()
            new_char_node.states.remove(State.SITTING)
            yield state.change_state([ChangeNode(new_char_node)])


class FindExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        current_obj = current_line.object()

        # select objects based on current_obj
        for node in state.select_nodes(current_obj):
            if self.check_find(state, node):
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(node), add_reverse=True)],
                    node,
                    current_obj
                )

    def check_find(self, state: EnvironmentState, node: GraphNode):
        return _is_character_close_to(state, node)


class WalkExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        current_obj = current_line.object()

        # select objects based on current_obj
        for node in state.select_nodes(current_obj):
            if self.check_walk(state, node):
                yield state.change_state(
                    [DeleteEdges(CharacterNode(),
                                 [Relation.INSIDE, Relation.CLOSE, Relation.FACING],
                                 AnyNode()),
                     AddEdges(CharacterNode(), Relation.INSIDE, RoomNode(node)),
                     AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(node), add_reverse=True)],
                    node,
                    current_obj
                )

    def check_walk(self, state: EnvironmentState, node: GraphNode):
        char_node = _get_character_node(state)
        if State.SITTING in char_node.states:
            return False
        return True


class JoinedExecutor(ActionExecutor):

    def __init__(self, *args):
        self.executors = args

    def execute(self, script: Script, state: EnvironmentState):
        for e in self.executors:
            for s in e.execute(script, state):
                yield s


class GrabExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            new_relation = self.check_grabbable(state, node)
            if new_relation is not None:
                changes = [DeleteEdges(NodeInstance(node), Relation.all(), AnyNode()),
                           AddEdges(CharacterNode(), new_relation, NodeInstance(node))]
                new_close = _find_first_node_from(state, node, [Relation.ON, Relation.INSIDE, Relation.CLOSE])
                if new_close is not None:
                    changes.append(AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(new_close), add_reverse=True))
                yield state.change_state(changes)

    def check_grabbable(self, state: EnvironmentState, node: GraphNode) -> Optional[Relation]:
        if Property.GRABBABLE not in node.properties:
            return None
        if not state.evaluate(ExistsRelation(CharacterNode(), Relation.CLOSE, NodeInstanceFilter(node))):
            return None
        if state.evaluate(ExistsRelation(NodeInstance(node), Relation.INSIDE,
                                         NodeConditionFilter(And(NodeAttrIn(State.OPEN, 'states'),
                                                                 Not(IsRoomNode()))))):
            return None
        return _find_free_hand(state)


class OpenExecutor(ActionExecutor):

    def __init__(self, close: bool):
        self.close = close

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_openable(state, node):
                new_node = node.copy()
                new_node.states.discard(State.OPEN if self.close else State.CLOSED)
                new_node.states.add(State.CLOSED if self.close else State.OPEN)
                yield state.change_state([ChangeNode(new_node)])

    def check_openable(self, state: EnvironmentState, node: GraphNode):
        if Property.CAN_OPEN not in node.properties:
            return False
        if not _is_character_close_to(state, node):
            return False
        if _find_free_hand(state) is None:
            return False
        s = State.OPEN if self.close else State.CLOSED
        return s in node.states


class PutExecutor(ActionExecutor):

    def __init__(self, inside):
        self.inside = inside

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        src_node = state.get_state_node(current_line.object())
        dest_node = state.get_state_node(current_line.subject())
        if src_node is not None and dest_node is not None:
            if self.check_puttable(state, src_node, dest_node):
                new_rel = Relation.INSIDE if self.inside else Relation.ON
                yield state.change_state(
                    [DeleteEdges(CharacterNode(), [Relation.HOLDS_LH, Relation.HOLDS_RH], NodeInstance(src_node)),
                     AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(dest_node), add_reverse=True),
                     AddEdges(NodeInstance(src_node), new_rel, NodeInstance(dest_node))]
                )

    def check_puttable(self, state: EnvironmentState, src_node: GraphNode, dest_node: GraphNode):
        hand_rel = _find_holding_hand(state, src_node)
        if hand_rel is None:
            return False
        if not _is_character_close_to(state, dest_node):
            return False
        if self.inside:
            return Property.CAN_OPEN not in dest_node.properties or \
                   State.OPEN in dest_node.states
        return True


class SwitchExecutor(ActionExecutor):

    def __init__(self, switch_on: bool):
        self.switch_on = switch_on

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_switchable(state, node):
                new_node = node.copy()
                new_node.states.discard(State.OFF if self.switch_on else State.ON)
                new_node.states.add(State.ON if self.switch_on else State.OFF)
                yield state.change_state([ChangeNode(new_node)])

    def check_switchable(self, state: EnvironmentState, node: GraphNode):
        if Property.HAS_SWITCH not in node.properties:
            return False
        if not _is_character_close_to(state, node):
            return False
        if _find_free_hand(state) is None:
            return False
        s = State.OFF if self.switch_on else State.ON
        return s in node.states


class DrinkExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_drinkable(state, node):
                yield state.change_state([])

    def check_drinkable(self, state: EnvironmentState, node: GraphNode):
        if Property.DRINKABLE not in node.properties:
            return False
        hand_rel = _find_holding_hand(state, node)
        if hand_rel is None:
            return False
        return True


# General checks and helpers

def _is_character_close_to(state: EnvironmentState, node: Node):
    if state.evaluate(ExistsRelation(CharacterNode(), Relation.CLOSE, NodeInstanceFilter(node))):
        return True
    for close_node in state.get_nodes_from(_get_character_node(state), Relation.CLOSE):
        if state.evaluate(ExistsRelation(NodeInstance(close_node), Relation.CLOSE, NodeInstanceFilter(node))):
            return True
    return False


def _get_character_node(state: EnvironmentState):
    chars = state.get_nodes_by_attr('class_name', 'character')
    return None if len(chars) == 0 else chars[0]


def _get_room_node(state: EnvironmentState, node: Node):
    for n in state.get_nodes_from(node, Relation.INSIDE):
        if n.category == 'Rooms':
            return n
    return None


def _find_first_node_from(state: EnvironmentState, node: Node, relations: List[Relation]):
    for r in relations:
        nl = state.get_nodes_from(node, r)
        if len(nl) > 0:
            return nl[0]
    return None


def _find_free_hand(state: EnvironmentState):
    if not state.evaluate(ExistsRelation(CharacterNode(), Relation.HOLDS_RH, AnyNodeFilter())):
        return Relation.HOLDS_RH
    if not state.evaluate(ExistsRelation(CharacterNode(), Relation.HOLDS_LH, AnyNodeFilter())):
        return Relation.HOLDS_LH
    return None


def _find_holding_hand(state: EnvironmentState, node: Node):
    if state.evaluate(ExistsRelation(CharacterNode(), Relation.HOLDS_RH, NodeInstanceFilter(node))):
        return Relation.HOLDS_RH
    if state.evaluate(ExistsRelation(CharacterNode(), Relation.HOLDS_LH, NodeInstanceFilter(node))):
        return Relation.HOLDS_LH
    return None

# ScriptExecutor
###############################################################################


class ScriptExecutor(object):

    _action_executors = {
        Action.GOTO: WalkExecutor(),
        Action.FIND: JoinedExecutor(FindExecutor(), WalkExecutor()),
        Action.SIT: SitExecutor(),
        Action.STANDUP: StandUpExecutor(),
        Action.GRAB: GrabExecutor(),
        Action.OPEN: OpenExecutor(False),
        Action.CLOSE: OpenExecutor(True),
        Action.PUT: PutExecutor(False),
        Action.PUTIN: PutExecutor(True),
        Action.SWITCHON: SwitchExecutor(True),
        Action.SWITCHOFF: SwitchExecutor(False),
        Action.DRINK: DrinkExecutor()
    }

    def __init__(self, graph: EnvironmentGraph, name_equivalence, object_placing=None, properties_data=None):
        self.graph = graph
        self.name_equivalence = name_equivalence
        self.object_placing = object_placing
        self.properties_data = properties_data
        self.processing_time_limit = 10  # 10 seconds
        self.processing_limit = 0

    def execute(self, script: Script, prepare: StatePrepare=None):
        self.processing_limit = time.time() + self.processing_time_limit
        init_state = EnvironmentState(self.graph, self.name_equivalence)
        if prepare is not None:
                prepare.apply_changes(init_state, script=script)
            # if self.object_placing is None or self.properties_data is None:
            #     raise ExecutionException('Can not prepare script, "object_placing" or '
            #                              '"properties_data" are not set')
            # _prepare_state(init_state, script, self.name_equivalence, self.object_placing, self.properties_data)
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


# state preparation

_DEFAULT_PROPERTY_STATES = {Property.HAS_SWITCH: State.OFF,
                            Property.CAN_OPEN: State.CLOSED}


def _prepare_state(state: EnvironmentState, script: Script, name_equivalence, object_placing, properties_data):
    state_classes = {n.class_name for n in state.get_nodes()}
    script_classes = {so.name for sl in script for so in sl.parameters}
    missing_classes = set()
    for sc in script_classes:
        if sc not in state_classes and len(set(name_equivalence.get(sc, [])) & state_classes) == 0:
            missing_classes.add(sc)
    if len(missing_classes) > 0:
        for mc in missing_classes:
            if mc not in object_placing:
                raise ExecutionException('No placing information for "{0}"', mc)
            if mc not in properties_data:
                raise ExecutionException('No properties data for "{0}"', mc)
            new_node_id = state.get_max_node_id() + 1
            for pi in object_placing[mc]:
                dest = pi['destination']
                room_name = pi['room']
                properties = properties_data.get(mc, [])
                placed = False
                for dest_node in state.get_nodes_by_attr('class_name', dest):
                    if room_name is None:
                        new_node = _create_node(new_node_id, mc, properties)
                        _change_state(state, new_node, dest_node, [])
                        new_node_id += 1
                        placed = True
                        break
                    else:
                        room_node = _get_room_node(state, dest_node)
                        if room_node is not None and room_node.class_name == room_name:
                            new_node = _create_node(new_node_id, mc, properties)
                            _change_state(state, new_node, dest_node,
                                          [AddEdges(NodeInstance(new_node), Relation.INSIDE, NodeInstance(room_node))])
                            new_node_id += 1
                            placed = True
                            break
                if placed:
                    break


def _create_node(node_id: int, class_name: str, properties):
    states = [_DEFAULT_PROPERTY_STATES[p] for p in properties if p in _DEFAULT_PROPERTY_STATES]
    return GraphNode(node_id, class_name, None, properties, states, None, None)


def _change_state(state: EnvironmentState, new_node: GraphNode, dest_node: Node, add_changers: List[StateChanger]):
    changers = [AddNode(new_node),
                AddEdges(NodeInstance(new_node), Relation.ON, NodeInstance(dest_node)),
                AddEdges(NodeInstance(new_node), Relation.CLOSE, NodeInstance(dest_node), add_reverse=True)]
    changers.extend(add_changers)
    state.apply_changes(changers)


# Exception
###############################################################################

class ExecutionException(common.Error):
    pass


