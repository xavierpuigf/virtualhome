from enum import Enum
from abc import abstractmethod
from typing import List

from common import TimeMeasurement
from scripts import ScriptObject

# {'bounding_box': {'center': [-3.629491, 0.9062717, -9.543596],
#   'size': [0.220000267, 0.00999999, 0.149999619]},
#  'category': 'Props',
#  'class_name': 'notes',
#  'id': 334,
#  'prefab_name': 'Notes_1',
#  'states': []}

# Enums
###############################################################################


class State(Enum):
    CLOSED = 1
    OPEN = 2
    ON = 3
    OFF = 4


class Relation(Enum):
    ON = 1
    INSIDE = 2
    BETWEEN = 3
    CLOSE = 4
    FACING = 5

    @classmethod
    def all(cls):
        return list(Relation)


class Property(Enum):
    SITTABLE = 1
    GRABBABLE = 2
    OPENABLE = 3
    SWITCHABLE = 4


# EnvironmentGraph, nodes, edges and related structures
###############################################################################


class Bounds(object):
    def __init__(self, center, size):
        self.center = center
        self.size = size


class Node(object):
    def __init__(self, id):
        self.id = id


class GraphNode(Node):
    def __init__(self, id, class_name, category, properties, states, prefab_name, bounding_box):
        super().__init__(id)
        self.class_name = class_name
        self.category = category
        self.properties = properties
        self.states = states
        self.prefab_name = prefab_name
        self.bounding_box = bounding_box

    def __str__(self):
        return '<{}> ({})'.format(self.class_name, self.prefab_name)

    @staticmethod
    def from_dict(d):
        return GraphNode(d['id'], d['class_name'], d['category'],
                         [Property[s.upper()] for s in d['properties']],
                         [State[s.upper()] for s in d['states']],
                         d['prefab_name'], Bounds(**d['bounding_box']))


class GraphEdge(object):
    def __init__(self, from_node: GraphNode, relation: Relation, to_node: GraphNode):
        self.from_node = from_node
        self.relation = relation
        self.to_node = to_node


class EnvironmentGraph(object):
    def __init__(self, dictionary):
        self._nodes = []  # type: List[GraphNode]
        self._edge_map = {}
        self._node_map = {}
        self._class_name_map = {}
        self._from_dictionary(dictionary)

    def _from_dictionary(self, d):
        self._nodes = [GraphNode.from_dict(n) for n in d['nodes']]
        for n in self._nodes:
            self._node_map[n.id] = n
            self._class_name_map.setdefault(n.class_name, []).append(n)
        edges = [(ed['from_id'], Relation[ed['relation_type'].upper()], ed['to_id'])
                 for ed in d['edges']]
        for from_id, relation, to_id in edges:
            es = self._edge_map.setdefault((from_id, relation), {})
            es[to_id] = self._node_map[to_id]

    def get_nodes(self):
        return self._nodes

    def get_nodes_by_attr(self, attr: str, value):
        if attr == 'class_name':
            for node in self._class_name_map.get(value, []):
                yield node
        else:
            for node in self._nodes:
                if getattr(node, attr) == value:
                    yield node

    def get_node(self, node):
        return self._node_map.get(node.id, None)

    def get_nodes_from(self, from_node: Node, relation: Relation):
        return self._get_node_maps_from(from_node, relation).values()

    def _get_node_maps_from(self, from_node: Node, relation: Relation):
        return self._edge_map.get((from_node.id, relation), {})

    def has_edge(self, from_node: Node, relation: Relation, to_node: Node):
        return to_node.id in self._get_node_maps_from(from_node, relation)


# EnvironmentState, state changes
###############################################################################


class ChangeType(Enum):
    ADD_NODE = 0
    DELETE_NODE = 1
    ADD_EDGE = 2
    DELETE_EDGE = 3


class StateChange(object):

    def __init__(self, change_type: ChangeType, change_object):
        self.type = change_type
        self.object = change_object

    def is_add_node(self, node: Node):
        return self.type == ChangeType.ADD_NODE and self.object.id == node.id

    def of_add_node(self):
        return self.object if self.type == ChangeType.ADD_NODE else None

    def is_delete_node(self, node: Node):
        return self.type == ChangeType.DELETE_NODE and self.object.id == node.id

    def of_delete_node(self):
        return self.object if self.type == ChangeType.DELETE_NODE else None

    def is_add_edge(self, from_node: Node, relation: Relation, to_node: Node):
        return (self.type == ChangeType.ADD_EDGE and self.object.from_node.id == from_node.id and
                self.object.relation == relation and self.object.to_node.id == to_node.id)

    def of_add_edge_from(self, from_node: Node, relation: Relation):
        if (self.type == ChangeType.ADD_EDGE and self.object.from_node.id == from_node.id and
                self.object.relation == relation):
            return self.object.to_node
        else:
            return None

    def is_delete_edge(self, from_node: Node, relation: Relation, to_node: Node):
        return (self.type == ChangeType.DELETE_EDGE and self.object.from_node.id == from_node.id and
                self.object.relation == relation and self.object.to_node.id == to_node.id)

    def of_delete_edge_from(self, from_node: Node, relation: Relation):
        if (self.type == ChangeType.DELETE_EDGE and self.object.from_node.id == from_node.id and
                self.object.relation == relation):
            return self.object.to_node
        else:
            return None


class EnvironmentState(object):

    def __init__(self, graph: EnvironmentGraph):
        self._graph = graph
        self._script_objects = {}  # (name, instance) -> node id
        self._changes = []  # type: List[StateChange]

    def evaluate(self, lvalue: 'LogicalValue'):
        return lvalue.evaluate(self)

    def select_nodes(self, obj: ScriptObject):
        """Enumerate nodes satisfying script object condition. If object was already
        discovered, return node
        """
        node = self._script_objects.get((obj.name, obj.instance), None)
        if node is not None:
            return [node]
        else:
            return self.get_nodes_by_attr('class_name', obj.name)

    def get_state_node(self, obj: ScriptObject):
        node_id = self._script_objects.get((obj.name, obj.instance), -1)
        return None if node_id < 0 else self.get_node(Node(node_id))

    def has_edge(self, from_node: Node, relation: Relation, to_node: Node):
        tm = TimeMeasurement.start('get_edge - changes')
        for change in reversed(self._changes):
            if change.is_delete_edge(from_node, relation, to_node):
                return False
            elif change.is_add_edge(from_node, relation, to_node):
                return True
        TimeMeasurement.stop(tm)
        return self._graph.has_edge(from_node, relation, to_node)

    def get_node(self, node: Node):
        for change in reversed(self._changes):
            if change.is_delete_node(node):
                return None
            elif change.is_add_node(node):
                return change.object()
        return self._graph.get_node(node)

    def nodes_from(self, from_node: Node, relation: Relation):
        deleted = set()  # deleted node ids
        for change in reversed(self._changes):
            to_node = change.of_delete_edge_from(from_node, relation)
            if to_node:
                deleted.add(to_node.id)
                continue
            to_node = change.of_add_edge_from(from_node, relation)
            if to_node and to_node.id not in deleted:
                yield to_node
        for to_node in self._graph.get_nodes_from(from_node, relation):
            if to_node.id not in deleted:
                yield to_node

    def get_nodes(self):
        deleted = set()  # deleted
        for change in reversed(self._changes):
            n = change.of_delete_node()
            if n:
                deleted.add(n.id)
                continue
            n = change.of_add_node()
            if n and n.id not in deleted:
                yield n
        for n in self._graph.get_nodes():
            if n.id not in deleted:
                yield n

    def get_nodes_by_attr(self, attr: str, value):
        deleted = set()  # deleted
        for change in reversed(self._changes):
            n = change.of_delete_node()
            if n:
                deleted.add(n.id)
                continue
            n = change.of_add_node()
            if n and n.id not in deleted and getattr(n, attr) == value:
                yield n
        for n in self._graph.get_nodes_by_attr(attr, value):
            if n.id not in deleted:
                yield n

    def change_state(self, changers: List['StateChanger'], node: Node, obj: ScriptObject = None):
        tm = TimeMeasurement.start('change_state')
        new_state = EnvironmentState(self._graph)
        new_state._changes = self._changes.copy()
        new_state._script_objects = self._script_objects.copy()
        if obj is not None:
            new_state._script_objects[(obj.name, obj.instance)] = node.id
        for changer in changers:
            for change in changer.enumerate_changes(self):
                new_state._changes.append(change)
        TimeMeasurement.stop(tm)
        return new_state


# NodeEnumerator-s
###############################################################################


class NodeEnumerator(object):

    @abstractmethod
    def enumerate(self, state: EnvironmentState):
        pass


class AnyNode(NodeEnumerator):

    def enumerate(self, state: EnvironmentState):
        return state.get_nodes()


class NodeInstance(NodeEnumerator):

    def __init__(self, node: Node):
        self.node = node

    def enumerate(self, state: EnvironmentState):
        yield state.get_node(self.node)


class RelationFrom(NodeEnumerator):

    def __init__(self, from_node: Node, relation: Relation):
        self.from_node = from_node
        self.relation = relation

    def enumerate(self, state: EnvironmentState):
        return state.nodes_from(self.from_node, self.relation)


class CharacterNode(NodeEnumerator):

    def enumerate(self, state: EnvironmentState):
        return state.get_nodes_by_attr('class_name', 'character')


class RoomNode(NodeEnumerator):

    def __init__(self, node: Node):
        self.node = node

    def enumerate(self, state: EnvironmentState):
        for n in state.nodes_from(self.node, Relation.INSIDE):
            if n.category == 'Rooms':
                yield n


# LogicalValue-s
###############################################################################


class LogicalValue(object):

    @abstractmethod
    def evaluate(self, state: EnvironmentState):
        pass


class Not(LogicalValue):

    def __init__(self, value1: LogicalValue):
        self.value1 = value1

    def evaluate(self, state: EnvironmentState):
        return not self.value1.evaluate(state)


class And(LogicalValue):

    def __init__(self, value1: LogicalValue, value2: LogicalValue):
        self.value1 = value1
        self.value2 = value2

    def evaluate(self, state: EnvironmentState):
        return self.value1.evaluate(state) and self.value2.evaluate(state)


class NodeState(LogicalValue):

    def __init__(self, node: Node, node_state: State):
        self.node = node
        self.node_state = node_state

    def evaluate(self, state: EnvironmentState):
        gn = state.get_node(self.node)
        return False if gn is None else self.node_state in gn.state


class NodeProperty(LogicalValue):

    def __init__(self, node: Node, node_property: Property):
        self.node = node
        self.node_property = node_property

    def evaluate(self, state: EnvironmentState):
        gn = state.get_node(self.node)
        return False if gn is None else self.node_property in gn.properties


class ExistsRelation(LogicalValue):

    def __init__(self, from_nodes: NodeEnumerator, relation: Relation, to_nodes: NodeEnumerator):
        self.from_nodes = from_nodes
        self.relation = relation
        self.to_nodes = to_nodes

    def evaluate(self, state: EnvironmentState):
        for fn in self.from_nodes.enumerate(state):
            for tn in self.to_nodes.enumerate(state):
                if state.has_edge(fn, self.relation, tn):
                    return True
        return False


# StateChanger-s
###############################################################################


class StateChanger(object):

    @abstractmethod
    def enumerate_changes(self, state: EnvironmentState):
        pass


class AddEdges(StateChanger):

    def __init__(self, from_node: NodeEnumerator, relation: Relation, to_node: NodeEnumerator):
        self.from_node = from_node
        self.relation = relation
        self.to_node = to_node

    def enumerate_changes(self, state: EnvironmentState):
        tm = TimeMeasurement.start('AddEdges')
        for n1 in self.from_node.enumerate(state):
            for n2 in self.to_node.enumerate(state):
                yield StateChange(ChangeType.ADD_EDGE, GraphEdge(n1, self.relation, n2))
        TimeMeasurement.stop(tm)


class DeleteEdges(StateChanger):

    def __init__(self, from_node: NodeEnumerator, relations, to_node: NodeEnumerator):
        self.from_node = from_node
        self.relations = relations
        self.to_node = to_node

    def enumerate_changes(self, state: EnvironmentState):
        tm = TimeMeasurement.start('DeleteEdges')
        for n1 in self.from_node.enumerate(state):
            for e in self.relations:
                for n2 in self.to_node.enumerate(state):
                    yield StateChange(ChangeType.DELETE_EDGE, GraphEdge(n1, e, n2))
        TimeMeasurement.stop(tm)
