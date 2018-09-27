import random
from environment import *
from common import Error
from scripts import Action, Script


class StatePrepare(StateChanger):

    def __init__(self, properties_data):
        self.properties_data = properties_data
        self.changers = []

    def add_changer(self, changer: StateChanger):
        self.changers.append(changer)

    def apply_changes(self, state: EnvironmentState, **kwargs):
        for changer in self.changers:
            changer.apply_changes(state, properties_data=self.properties_data)


class RandomObjectPrepare(StateChanger):

    def __init__(self, name_equivalence, properties_data, object_placing,
                 random_seed=None, missing_choices=1, other_choices=0):
        # Each missing object from the script is selected randomly
        # missing_choices-times
        # Objects from the object_placing are selected other_choices-times
        self.name_equivalence = name_equivalence
        self.properties_data = properties_data
        self.object_placing = object_placing
        self.missing_choices = missing_choices
        self.other_choices = other_choices
        random.seed(random_seed)

    def apply_changes(self, state: EnvironmentState, **kwargs):
        assert 'script' in kwargs
        script = kwargs['script']
        self._add_missing_classes(state, script)

    def _add_missing_classes(self, state: EnvironmentState, script: Script):
        state_classes = {n.class_name for n in state.get_nodes()}
        script_classes = {so.name for sl in script for so in sl.parameters}
        missing_classes = set()
        for sc in script_classes:
            if sc not in state_classes and len(set(self.name_equivalence.get(sc, [])) & state_classes) == 0:
                missing_classes.add(sc)
        for mc in missing_classes:
            if mc not in self.object_placing:
                raise Error('No placing information for "{0}"', mc)
            if mc not in self.properties_data:
                raise Error('No properties data for "{0}"', mc)
            placings = [random.choice(self.object_placing[mc]) for i in range(0, self.missing_choices)]
            properties = self.properties_data.get(mc, [])
            for placing in placings:
                dest = placing['destination']
                states = _random_property_states(properties)
                changer = AddObject(mc, Destination(Relation.ON, ClassNameNode(dest)), states,
                                    randomize=True, choices=1)
                changer.apply_changes(state, properties_data=self.properties_data)
        


class AddObject(StateChanger):

    def __init__(self, class_name: str, destination: 'Destination', states: List[State]=None,
                 randomize=False, choices=1):
        self.class_name = class_name
        self.destination = destination
        self.states = states
        self.randomize = randomize
        self.choices = choices

    def apply_changes(self, state: EnvironmentState, **kwargs):
        assert 'properties_data' in kwargs
        properties_data = kwargs['properties_data']
        properties = properties_data.get(self.class_name, [])
        destinations = list(self.destination.nodes.enumerate(state))
        if self.randomize and len(destinations) > 0:
            destinations = [random.choice(destinations) for i in range(0, self.choices)]
        else:
            destinations = destinations[0:self.choices + 1]
        for dest_node in destinations:
            if self.destination.node_filter.evaluate(state, node=dest_node):
                new_node = _create_node(self.class_name, properties, self.states)
                _change_state(state, new_node, dest_node, [])


class Destination(object):

    def __init__(self, relation: Relation, nodes: NodeEnumerator, node_filter: LogicalValue=Constant(True)):
        self.relation = relation
        self.nodes = nodes
        self.node_filter = node_filter


_DEFAULT_PROPERTY_STATES = {Property.HAS_SWITCH: State.OFF,
                            Property.CAN_OPEN: State.CLOSED}


_PROPERTY_STATES = {Property.HAS_SWITCH: [State.ON, State.OFF],
                    Property.CAN_OPEN: [State.CLOSED, State.OPEN]}


def _random_property_states(properties: List[Property]):
    return [random.choice(_PROPERTY_STATES[p]) for p in properties if p in _PROPERTY_STATES]


def _create_node(class_name: str, properties, states=None):
    if states is None:
        states = [_DEFAULT_PROPERTY_STATES[p] for p in properties if p in _DEFAULT_PROPERTY_STATES]
    return GraphNode(0, class_name, None, properties, states, None, None)


def _change_state(state: EnvironmentState, new_node: GraphNode, dest_node: Node,
                  add_changers: List[StateChanger]):
    changers = [AddNode(new_node),
                AddEdges(NodeInstance(new_node), Relation.ON, NodeInstance(dest_node)),
                AddEdges(NodeInstance(new_node), Relation.CLOSE, NodeInstance(dest_node), add_reverse=True),
                AddEdges(NodeInstance(new_node), Relation.INSIDE, RoomNode(dest_node))]
    changers.extend(add_changers)
    state.apply_changes(changers)
