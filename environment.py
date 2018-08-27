from enum import Enum
from abc import abstractmethod
from typing import Collection

from scripts import ScriptObject

# {'bounding_box': {'center': [-3.629491, 0.9062717, -9.543596],
#   'size': [0.220000267, 0.00999999, 0.149999619]},
#  'category': 'Props',
#  'class_name': 'notes',
#  'id': 334,
#  'prefab_name': 'Notes_1',
#  'states': []}


class State(Enum):
    CLOSED = 0,
    OPEN = 1,
    ON = 2
    OFF = 3


class Relation(Enum):
    ON = 0,
    INSIDE = 1,
    BETWEEN = 2


class Property(Enum):
    SITTABLE = 0,
    GRABBABLE = 1,
    OPENABLE = 2,
    SWITCHABLE = 3


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

    @staticmethod
    def from_dict(d):
        return GraphNode(d['id'], d['class_name'], d['category'],
                         [Property[s.upper()] for s in d['properties']],
                         [State[s.upper()] for s in d['states']],
                         d['prefab_name'], Bounds(**d['bounding_box']))


class GraphEdge(object):
    def __init__(self, from_node: GraphNode, relation: GraphNode, to_node: GraphNode):
        self.from_node = from_node
        self.relation = relation
        self.to_node = to_node

    @staticmethod
    def from_dict(d):
        return GraphEdge(d['from_id'], Relation[d['relation'].upper()], d['to_id'])


class EnvironmentGraph(object):
    def __init__(self, nodes: Collection[GraphNode], edges: Collection[GraphEdge]):
        self._nodes = nodes
        self._edges = edges
        self._edge_map = {}
        self._node_map = {}
        self._class_name_map = {}
        self._init_maps()

    def _init_maps(self):
        for e in self._edges:
            es = self._edge_map.setdefault((e.from_node.id, e.relation), {})
            es[e.to_node.id] = e
        for n in self._nodes:
            self._node_map[n.id] = n
            self._class_name_map.setdefault(n.class_name, []).append(n)

    def get_nodes(self):
        return self._nodes

    def get_nodes_by_attr(self, attr: str, value):
        if attr == 'class_name':
            return self._class_name_map.get(value, [])
        else:
            for node in self._nodes:
                if getattr(node, attr) == value:
                    yield node

    def get_node(self, node):
        return self._node_map.get(node.id, None)

    def get_edge(self, from_node: Node, relation: Relation, to_node: Node):
        to_map = self._edge_map.get((from_node.id, relation), {})
        return to_map.get(to_node.id, None)

    def get_edges_from(self, from_node: Node, relation: Relation):
        to_map = self._edge_map.get((from_node.id, relation), {})
        return to_map.values()

    def has_edge(self, from_node: Node, relation: Relation, to_node: Node):
        return self.get_edge(from_node, relation, to_node) is not None

    @staticmethod
    def from_dict(d):
        nodes = [GraphNode.from_dict(n) for n in d['nodes']]
        edges = [GraphEdge.from_dict(e) for e in d['edges']]
        return EnvironmentGraph(nodes, edges)


class ChangeType(Enum):
    ADD_NODE = 0,
    DELETE_NODE = 1,
    ADD_EDGE = 2,
    DELETE_EDGE = 3


class EnvironmentState(object):

    class Change(object):

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

    def __init__(self, graph: EnvironmentGraph):
        self._graph = graph
        self._script_objects = {}  # (name, instance) -> node id
        self._changes = []

    def evaluate(self, lvalue: 'LogicalValue'):
        return lvalue.evaluate(self)

    def select_nodes(self, obj: ScriptObject):
        """Enumerate nodes satisfying script object condition. If object was already
        discovered, return node
        """
        node = self._script_objects.get((obj.name, obj.instance), None)
        if node is not None:
            yield node
        else:
            return self.get_nodes_by_attr('class_name', obj.name)

    def get_edge(self, from_node: Node, relation: Relation, to_node: Node):
        for change in reversed(self._changes):
            if change.is_delete_edge(from_node, relation, to_node):
                return None
            elif change.is_add_edge(from_node, relation, to_node):
                return change.object()
        return self._graph.get_edge(from_node, relation, to_node)

    def has_edge(self, from_node: Node, relation: Relation, to_node: Node):
        return self.get_edge(from_node, relation, to_node) is not None

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
        for edge in self._graph.get_edges_from(from_node, relation):
            if edge.to_node.id not in deleted:
                yield edge.to_node

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


#
#  <character> [close] <object>
#  and  <object> [sittable]
#
#  CHAR = character node
#  find_node(RELATION_FROM(CHAR, Relation.CLOSE)) -> [nodes close to CHAR]
#  find_node(AND(RELATION_FROM(CHAR, Relation.CLOSE), STATE(State.SITTABLE))
#
#  <character> [close] <object>
#  and  <object> [sittable]
#  and  not Exists <object2>: <object2> [on] <object>
#
#  CHAR = character node
#  find_node(AND(RELATION_FROM(CHAR, Relation.CLOSE), STATE(State.SITTABLE), )
#


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


# execute
#   goto chair
#   sit chair
#
#   state = State(graph)
#   action1 = GOTO('chair')
#
#   for n in graph.get_nodes(ClassNameNode('chair')):
#       graph.remove_edges(Node(char_node), 'close', AnyNode())
#       graph.remove_edges_u(Node(char_node), 'inside', RoomNode())
#       graph.add_edge(char_node, 'close', n)
#       graph.add_edge(char_node, 'inside', RoomNode(n))
#       state = State(graph, {'chair': n})
#       yield state
#
#   state
#   action2 = SIT('chair')
#
#   graph.check_condition(And(NodeState(NodeId(StateObject('chair', 1)), 'sittable'),
#       NotExistRelation(AnyNode(), 'on', NodeId(StateObject('chair', 1)))))
#
#
#

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
