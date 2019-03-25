import random
from typing import Iterable

from evolving_graph.environment import *
from evolving_graph.execution import _get_room_node
from evolving_graph.common import Error, TimeMeasurement



class StatePrepare(StateChanger):

    def __init__(self, properties_data, changers: Iterable[StateChanger]=None):
        self.properties_data = properties_data
        self.changers = [] if changers is None else changers

    def add_changer(self, changer: StateChanger):
        self.changers.append(changer)

    def apply_changes(self, state: EnvironmentState, **kwargs):
        for changer in self.changers:
            changer.apply_changes(state, properties_data=self.properties_data)


class AddMissingScriptObjects(StateChanger):

    def __init__(self, name_equivalence, properties_data, object_placing, choices=1):
        # Each missing object from the script is selected randomly
        # missing_choices-times
        # Objects from the object_placing are selected other_choices-times
        self.name_equivalence = name_equivalence
        self.properties_data = properties_data
        self.object_placing = object_placing
        self.choices = choices

    def apply_changes(self, state: EnvironmentState, **kwargs):
        assert 'script' in kwargs
        script = kwargs['script']
        state_classes = {n.class_name for n in state.get_nodes()}
        script_classes = {so.name for sl in script for so in sl.parameters}
        missing_classes = set()
        for sc in script_classes:
            if sc not in state_classes and len(set(self.name_equivalence.get(sc, [])) & state_classes) == 0:
                missing_classes.add(sc)
        for cn in missing_classes:
            if cn not in self.object_placing:
                raise Error('No placing information for "{0}"', cn)
            placings = self.object_placing[cn]
            random.shuffle(placings)
            properties = self.properties_data.get(cn, [])
            for placing in placings:
                dest = placing['destination']
                states = _random_property_states(properties)
                changer = AddObject(cn, Destination(Relation.ON, ClassNameNode(dest)), states,
                                    randomize=True, choices=1)
                changer.apply_changes(state, properties_data=self.properties_data)


class AddRandomObjects(StateChanger):

    def __init__(self, properties_data, object_placing, choices: int):
        self.properties_data = properties_data
        self.object_placing = object_placing
        self.choices = choices

    def apply_changes(self, state: EnvironmentState, **kwargs):
        available = list(self.object_placing.keys())
        random.shuffle(available)
        placed_objects = 0
        for cn in available:
            if placed_objects >= self.choices:
                break
            properties = self.properties_data.get(cn, [])
            placing = random.choice(self.object_placing[cn])
            dest = placing['destination']
            states = _random_property_states(properties)
            changer = AddObject(cn, Destination(Relation.ON, ClassNameNode(dest)), states,
                                randomize=True, choices=1)
            placed_objects += changer.apply_changes(state, properties_data=self.properties_data)


class ChangeObjectStates(StateChanger):

    def __init__(self, properties_data):
        self.properties_data = properties_data

    def apply_changes(self, state: EnvironmentState, **kwargs):
        for node in state.get_nodes():
            for p in node.properties & _PROPERTY_STATES.keys():
                possible_states = _PROPERTY_STATES[p]
                node.states -= set(possible_states)
                node.states.add(random.choice(possible_states))


class ChangeState(StateChanger):

    def __init__(self, class_name: str, states: Iterable[State], node_filter: LogicalValue=Constant(True)):
        self.class_name = class_name
        self.states = set(states)
        self.node_filter = node_filter

    def apply_changes(self, state: EnvironmentState, **kwargs):
        for node in ClassNameNode(self.class_name).enumerate(state):
            if self.node_filter.evaluate(state, node=node):
                node.states = self.states


class AddObject(StateChanger):

    def __init__(self, class_name: str, destination: 'Destination', states: Iterable[State]=None,
                 randomize=False, choices=1):
        self.class_name = class_name
        self.destination = destination
        self.states = states
        self.randomize = randomize
        self.choices = choices

    def apply_changes(self, state: EnvironmentState, **kwargs):
        assert 'properties_data' in kwargs
        tm = TimeMeasurement.start('AddObject-Preparation')
        properties_data = kwargs['properties_data']
        properties = properties_data.get(self.class_name, [])
        destinations = list(self.destination.nodes.enumerate(state))
        if self.randomize:
            random.shuffle(destinations)
        placed_objects = 0
        for dest_node in destinations:
            if placed_objects >= self.choices:
                break
            if self.destination.node_filter.evaluate(state, node=dest_node):
                new_node = _create_node(self.class_name, properties, self.states)
                _add_edges(state, new_node, self.destination.relation, dest_node, [])
                placed_objects += 1
        TimeMeasurement.stop(tm)
        return placed_objects


class Destination(object):

    def __init__(self, relation: Relation, nodes: NodeEnumerator, node_filter: LogicalValue=Constant(True)):
        self.relation = relation
        self.nodes = nodes
        self.node_filter = node_filter

    @classmethod
    def of(cls, class_name: str, relation: Relation, room_name: str=None):
        if room_name is None:
            return Destination(relation, ClassNameNode(class_name))
        else:
            return Destination(relation, ClassNameNode(class_name),
                               ExistsRelation(NodeParam(), Relation.INSIDE, NodeConditionFilter(IsRoomNode(room_name))) )

    @classmethod
    def on(cls, class_name: str, room_name: str=None):
        return cls.of(class_name, Relation.ON, room_name)

    @classmethod
    def inside(cls, class_name: str, room_name: str=None):
        return cls.of(class_name, Relation.INSIDE, room_name)


_DEFAULT_PROPERTY_STATES = {Property.HAS_SWITCH: State.OFF,
                            Property.CAN_OPEN: State.CLOSED,
                            Property.HAS_PLUG: State.PLUGGED_IN}


_PROPERTY_STATES = {Property.HAS_SWITCH: [State.ON, State.OFF],
                    Property.CAN_OPEN: [State.CLOSED, State.OPEN],
                    Property.HAS_PLUG: [State.PLUGGED_IN, State.PLUGGED_OUT]}


def _random_property_states(properties: Iterable[Property]):
    return [random.choice(_PROPERTY_STATES[p]) for p in properties if p in _PROPERTY_STATES]


def _create_node(class_name: str, properties, states=None):
    if states is None:
        states = [_DEFAULT_PROPERTY_STATES[p] for p in properties if p in _DEFAULT_PROPERTY_STATES]
    return GraphNode(id=0, class_name=class_name, category=None, properties=set(properties),
                     states=set(states), prefab_name=None, bounding_box=None)


def _add_edges(state: EnvironmentState, new_node: GraphNode, relation: Relation, dest_node: Node,
               add_changers: List[StateChanger]):

    room_node = _get_room_node(state, dest_node)
    changers = [AddNode(new_node),
                AddEdges(NodeInstance(new_node), relation, NodeInstance(dest_node)),
                AddEdges(NodeInstance(new_node), Relation.CLOSE, NodeInstance(dest_node), add_reverse=True),
                AddEdges(NodeInstance(new_node), Relation.INSIDE, NodeInstance(room_node))]
    changers.extend(add_changers)
    state.apply_changes(changers)
