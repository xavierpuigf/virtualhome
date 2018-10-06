import time
from typing import Optional

import common
from environment import *
from scripts import Action, Script
import ipdb


# ActionExecutor-s
###############################################################################


class ActionExecutor(object):

    @abstractmethod
    def execute(self, script: Script, state: EnvironmentState, info: dict):
        """
        :param script: future script, scripts.Script object containing script lines
            yet to be executed, has at least one item
        :param state: current state, environment.EnvironmentState object
        :return: enumerates possible states after execution of script_line
        """
        pass


class UnknownExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        raise ExecutionException("Execution of {0} is not supported", script[0].action)


class JoinedExecutor(ActionExecutor):

    def __init__(self, *args):
        self.executors = args

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        for e in self.executors:
            for s in e.execute(script, state, info):
                yield s


class FindExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        current_obj = current_line.object()

        # select objects based on current_obj
        for node in state.select_nodes(current_obj):
            if self.check_find(state, node, info):
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(node), add_reverse=True)],
                    node,
                    current_obj
                )

    def check_find(self, state: EnvironmentState, node: GraphNode, info: dict):
        
        if not _is_character_close_to(state, node):
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not closed to {}(id:{}) "[Find] <{}> ({})"'.format( \
                                        char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return False
        else:
            return 


class WalkExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        current_obj = current_line.object()

        # select objects based on current_obj
        for node in state.select_nodes(current_obj):
            if self.check_walk(state, node, info):
                yield state.change_state(
                    [DeleteEdges(CharacterNode(),
                                 [Relation.INSIDE, Relation.CLOSE, Relation.FACING],
                                 AnyNode(), delete_reverse=True),
                     AddEdges(CharacterNode(), Relation.CLOSE, BoxObjectNode(node), add_reverse=True), 
                     AddEdges(CharacterNode(), Relation.INSIDE, RoomNode(node)),
                     AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(node), add_reverse=True)],
                    node,
                    current_obj
                )

    def check_walk(self, state: EnvironmentState, node: GraphNode, info: dict):
        char_node = _get_character_node(state)
        if State.SITTING in char_node.states:
            info['error_message'] = '{}(id:{}) is sitting when executing "[Walk] <{}> ({})"'.format(char_node.class_name, char_node.id, 
                                                                            node.class_name, node.id)
            return False
        # char_room = _get_room_node(state, char_node)
        # node_room = _get_room_node(state, node)
        # if char_room.id != node_room.id:
        #     return not state.evaluate(
        #         ExistRelations(FilteredNodes(ClassNameNode('door'), NodeAttrIn(State.CLOSED, 'states')),
        #                        [(Relation.BETWEEN, NodeInstanceFilter(char_room)),
        #                         (Relation.BETWEEN, NodeInstanceFilter(node_room))])
        #     )
        return True


class SitExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_sittable(state, node, info):
                char_node = _get_character_node(state)
                new_char_node = char_node.copy()
                new_char_node.states.add(State.SITTING)
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.ON, NodeInstance(node)),
                     ChangeNode(new_char_node)]
                )
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[Sit] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_sittable(self, state: EnvironmentState, node: GraphNode, info: dict):
        char_node = _get_character_node(state)

        if not _is_character_close_to(state, node):
            info['error_message'] = '{}(id:{}) is not close to {}(id:{}) when executing [Sit] <{}> ({})'.format( \
                                    char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return False
        if State.SITTING in char_node.states:
            info['error_message'] = '{}(id:{}) is not sitting when executing [Sit] <{}> ({})'.format( \
                                    char_node.class_name, char_node.id, node.class_name, node.id)
            return False
        if Property.SITTABLE not in node.properties:
            info['error_message'] = '{}(id:{}) is not sittable when executing [Sit] <{}> ({})'.format( \
                                    node.class_name, node.id, node.class_name, node.id)
            return False
        if state.evaluate(ExistsRelation(AnyNode(), Relation.ON, NodeInstanceFilter(node))):
            info['error_message'] = 'something on the {}(id:{}) when executing [Sit] <{}> ({})'.format( \
                                    node.class_name, node.id, node.class_name, node.id)
            return False

        return True


class StandUpExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        char_node = _get_character_node(state)
        if State.SITTING in char_node.states:
            new_char_node = char_node.copy()
            new_char_node.states.remove(State.SITTING)
            yield state.change_state([ChangeNode(new_char_node)])
        else:
            info['error_message'] = '{}(id:{}) is not sitting when executing "Standup"'.format(char_node.class_name, char_node.id)


class GrabExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            new_relation = self.check_grabbable(state, node, info)
            if new_relation is not None:
                changes = [DeleteEdges(NodeInstance(node), Relation.all(), AnyNode()),
                           AddEdges(CharacterNode(), new_relation, NodeInstance(node))]
                new_close = _find_first_node_from(state, node, [Relation.ON, Relation.INSIDE, Relation.CLOSE])
                if new_close is not None:
                    changes.append(AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(new_close), add_reverse=True))
                yield state.change_state(changes)
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[Grab] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_grabbable(self, state: EnvironmentState, node: GraphNode, info: dict) -> Optional[Relation]:
        if Property.GRABBABLE not in node.properties:
            info['error_message'] = '{}(id:{}) is not grabbable when executing "[Grab] <{}> ({})"'.format( \
                                            node.class_name, node.id, node.class_name, node.id)
            return None
        if not state.evaluate(ExistsRelation(CharacterNode(), Relation.CLOSE, NodeInstanceFilter(node))):
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not close to {}(id:{}) when executing "[Grab] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return None
        if state.evaluate(ExistsRelation(NodeInstance(node), Relation.INSIDE,
                                         NodeConditionFilter(And(NodeAttrIn(State.CLOSED, 'states'),
                                                                 Not(IsRoomNode()))))):
            info['error_message'] = '{}(id:{}) is inside other closed thing when executing "[Grab] <{}> ({})"'.format( \
                                            node.class_name, node.id, node.class_name, node.id)
            return None

        new_relation = _find_free_hand(state)
        if new_relation is None:
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) does not have free hand when executing "[Grab] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, node.class_name, node.id)
            return None

        return new_relation


class OpenExecutor(ActionExecutor):

    def __init__(self, close: bool):
        """
            OpenExecutor: False
            CloseExecutor: True
        """
        self.close = close

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_openable(state, node, info):
                new_node = node.copy()
                new_node.states.discard(State.OPEN if self.close else State.CLOSED)
                new_node.states.add(State.CLOSED if self.close else State.OPEN)
                yield state.change_state([ChangeNode(new_node)])
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[Open] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)
    def check_openable(self, state: EnvironmentState, node: GraphNode, info: dict):

        if Property.CAN_OPEN not in node.properties:
            info['error_message'] = '{}(id:{}) can not be opened when executing "[Open] <{}> ({})"'.format( \
                                            node.class_name, node.id, node.class_name, node.id)
            return False

        if not _is_character_close_to(state, node):
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not close to {}()id:{} when executing "[Open] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return False
        if _find_free_hand(state) is None:
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) does have any free hand when executing "[Open] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, node.class_name, node.id)
            return False

        s = State.OPEN if self.close else State.CLOSED
        if s not in node.states:
            info['error_message'] = '{}(id:{}) is not {} when executing "[Open] <{}> ({})'.format( \
                                            node.class_name, node.id, s.name.lower(), node.class_name, node.id)
            return False
        return True


class PutExecutor(ActionExecutor):

    def __init__(self, inside):
        """
            PutExecutor: False
            PutInExecutor: True
        """
        self.inside = inside

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        src_node = state.get_state_node(current_line.object())
        dest_node = state.get_state_node(current_line.subject())
        if src_node is not None and dest_node is not None:
            if self.check_puttable(state, src_node, dest_node, info):
                new_rel = Relation.INSIDE if self.inside else Relation.ON
                yield state.change_state(
                    [DeleteEdges(CharacterNode(), [Relation.HOLDS_LH, Relation.HOLDS_RH], NodeInstance(src_node)),
                     AddEdges(CharacterNode(), Relation.CLOSE, NodeInstance(dest_node), add_reverse=True),
                     AddEdges(NodeInstance(src_node), new_rel, NodeInstance(dest_node))]
                )
        else:
            missing_object = current_line.object() if src_node is None else current_line.subject()
            info['error_message'] = '<{}> ({}) can not be found when executing "[Put] <{}> ({})"'.format( \
                                            missing_object.name, missing_object.instance, 
                                            missing_object.name, missing_object.instance)

    def check_puttable(self, state: EnvironmentState, src_node: GraphNode, dest_node: GraphNode, info: dict):
        hand_rel = _find_holding_hand(state, src_node)
        if hand_rel is None:
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not holding {}(id:{}) when executing "[Put] <{}> ({}) <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, src_node.class_name, src_node.id, 
                                            src_node.class_name, src_node.id, dest_node.class_name, dest_node.id)
            return False
        if not _is_character_close_to(state, dest_node):
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not close to {}(id:{}) when executing "[Put] <{}> ({}) <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, dest_node.class_name, dest_node.id, 
                                            src_node.class_name, src_node.id, dest_node.class_name, dest_node.id)
            return False
        if self.inside:
            if Property.CAN_OPEN not in dest_node.properties or \
                   State.OPEN in dest_node.states:
                return True
            else:
                info['error_message'] = '{}(id:{}) is not open or is not openable when executing "[Put] <{}> ({}) <{}> ({})"'.format( \
                                            dest_node.class_name, dest_node.id, 
                                            src_node.class_name, src_node.id, dest_node.class_name, dest_node.id)
                return False
        return True


class SwitchExecutor(ActionExecutor):

    def __init__(self, switch_on: bool):
        """
            SwitchOnExecutor: True
            SwitchOffExecutor: False
        """
        self.switch_on = switch_on

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_switchable(state, node, info):
                new_node = node.copy()
                new_node.states.discard(State.OFF if self.switch_on else State.ON)
                new_node.states.add(State.ON if self.switch_on else State.OFF)
                yield state.change_state([ChangeNode(new_node)])
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[Switch] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_switchable(self, state: EnvironmentState, node: GraphNode, info: dict):

        s = State.OFF if self.switch_on else State.ON
        if Property.HAS_SWITCH not in node.properties:
            info['error_message'] = '{}(id:{}) does not have switch when executing "[Switch{}] <{}> ({})"'.format( \
                                            node.class_name, node.id, s.name.capitalize(), node.class_name, node.id)
            return False
        if not _is_character_close_to(state, node):
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not close to {}(id:{}) when executing "[Switch{}] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, node.class_name, node.id, s.name.capitalize(), node.class_name, node.id)
            return False
        if _find_free_hand(state) is None:
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) does not have free hand when executing "[Switch{}] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, s.name.capitalize(), node.class_name, node.id)
            return False

        if s not in node.states:
            info['error_message'] = '{}(id:{}) is not {} when executing "[Switch{}] <{}> ({})"'.format( \
                                            node.class_name, node.id, s.name.lower(), s.name.capitalize(), node.class_name, node.id)
            return False

        return True


class DrinkExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_drinkable(state, node, info):
                yield state.change_state([])
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[Drink] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_drinkable(self, state: EnvironmentState, node: GraphNode, info: dict):
        if Property.DRINKABLE not in node.properties:
            info['error_message'] = '{}(id:{}) is not drinkable when executing "[Drink] <{}> ({})"'.format( \
                                            node.class_name, node.id, node.class_name, node.id)
            return False
        hand_rel = _find_holding_hand(state, node)
        if hand_rel is None:
            char_node = _get_character_node(state)
            info['error_message'] = '{}(id:{}) is not holding {}(id:{}) when executing "[Drink] <{}> ({})"'.format( \
                                            char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return False
        return True


class TurnToExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node =  state.get_state_node(current_line.object())
        if node is not None:
            if self.check_turn_to(state, node, info):
                yield state.change_state(
                    [AddEdges(CharacterNode(), Relation.FACING, NodeInstance(node))]
                )
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[TurnTo] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_turn_to(self, state: EnvironmentState, node: GraphNode, info: dict):
        char_node = _get_character_node(state)
        if not _is_character_close_to(state, node):
            info['error_message'] = '{}(id:{}) is not close to {}(id:{}) when executing [TurnTo] <{}> ({})'.format( \
                                    char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return False
        
        return True


class LookAtExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node =  state.get_state_node(current_line.object())
        if node is not None:
            if self.check_lookat(state, node, info):
                yield state.change_state([])
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[TurnTo] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_lookat(self, state: EnvironmentState, node: GraphNode, info: dict):
        char_node = _get_character_node(state)
        if not _is_character_face_to(state, node):
            info['error_message'] = '{}(id:{}) does not face {}(id:{}) when executing [TurnTo] <{}> ({})'.format( \
                                    char_node.class_name, char_node.id, node.class_name, node.id,  node.class_name, node.id)
            return False

        return True


class WipeExecutor(ActionExecutor):

    def execute(self, script: Script, state: EnvironmentState, info: dict):
        current_line = script[0]
        node = state.get_state_node(current_line.object())
        if node is not None:
            if self.check_wipe(state, node, info):
                yield state.change_state([])
        else:
            info['error_message'] = '<{}> ({}) can not be found when executing "[Wipe] <{}> ({})"'.format( \
                                            current_line.object().name, current_line.object().instance, 
                                            current_line.object().name, current_line.object().instance)

    def check_wipe(self, state: EnvironmentState, node: GraphNode, info: dict):
        char_node = _get_character_node(state)

        if not _is_character_close_to(state, node):
            info['error_message'] = '{}(id:{}) is not close to {}(id:{}) when executing [Wipe] <{}> ({})'.format( \
                                    char_node.class_name, char_node.id, node.class_name, node.id, node.class_name, node.id)
            return False

        if Property.SURFACES not in node.properties:
            info['error_message'] = '{}(id:{}) does not have surface when executing [Wipe] <{}> ({})'.format( \
                                    node.class_name, node.id, node.class_name, node.id)
            return False

        nodes_in_hands = _find_nodes_from(state, char_node, [Relation.HOLDS_RH, Relation.HOLDS_LH])
        if len(nodes_in_hands) == 0:
            info['error_message'] = '{}(id:{}) does not hold anything in hands when executing [Wipe] <{}> ({})'.format( \
                                    char_node.class_name, char_node.id, node.class_name, node.id)
            return 

        return True


# General checks and helpers

def _is_character_close_to(state: EnvironmentState, node: Node):
    if state.evaluate(ExistsRelation(CharacterNode(), Relation.CLOSE, NodeInstanceFilter(node))):
        return True
    for close_node in state.get_nodes_from(_get_character_node(state), Relation.CLOSE):
        if state.evaluate(ExistsRelation(NodeInstance(close_node), Relation.CLOSE, NodeInstanceFilter(node))):
            return True
    return False

def _is_character_face_to(state: EnvironmentState, node: Node):
    if state.evaluate(ExistsRelation(CharacterNode(), Relation.FACING, NodeInstanceFilter(node))):
        return True
    for face_node in state.get_nodes_from(_get_character_node(state), Relation.FACING):
        if state.evaluate(ExistsRelation(NodeInstance(face_node), Relation.FACING, NodeInstanceFilter(node))):
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

def _find_nodes_from(state: EnvironmentState, node: Node, relations: List[Relation]):
    nodes = []
    for r in relations:
        nl = state.get_nodes_from(node, r)
        nodes += nl
    return nodes

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
        Action.DRINK: DrinkExecutor(), 
        Action.LOOKAT: LookAtExecutor(), 
        Action.TURNTO: TurnToExecutor(), 
        Action.WIPE: WipeExecutor()
    }

    def __init__(self, graph: EnvironmentGraph, name_equivalence):
        self.graph = graph
        self.name_equivalence = name_equivalence
        self.processing_time_limit = 10  # 10 seconds
        self.processing_limit = 0
        self.info = {}

    def find_solutions(self, script: Script, init_changers: List[StateChanger]=None):
        self.processing_limit = time.time() + self.processing_time_limit
        init_state = EnvironmentState(self.graph, self.name_equivalence)
        _apply_initial_changers(init_state, script, init_changers)
        return self.find_solutions_rec(script, 0, init_state)

    def find_solutions_rec(self, script: Script, script_index: int, state: EnvironmentState):
        if script_index >= len(script):
            yield state
        future_script = script.from_index(script_index)
        for next_state in self.call_action_method(future_script, state):
            for rec_state_list in self.find_solutions_rec(script, script_index + 1, next_state):
                yield rec_state_list
            if time.time() > self.processing_limit:
                break

    def execute(self, script: Script, init_changers: List[StateChanger]=None):

        info = self.info
        state = EnvironmentState(self.graph, self.name_equivalence, instance_selection=True)
        _apply_initial_changers(state, script, init_changers)
        for i in range(len(script)):
            future_script = script.from_index(i)
            state = next(self.call_action_method(future_script, state, info), None)
            if state is None:
                return None
        return state

    @classmethod
    def call_action_method(cls, script: Script, state: EnvironmentState, info: dict={}):
        executor = cls._action_executors.get(script[0].action, UnknownExecutor())
        return executor.execute(script, state, info)

def _apply_initial_changers(state: EnvironmentState, script: Script, changers: List[StateChanger]=None):
    if changers is not None:
        for changer in changers:
            changer.apply_changes(state, script=script)


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


