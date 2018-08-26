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
    def __init__(self, id, class_name, category, states, prefab_name, bounding_box):
        super().__init__(id)
        self.class_name = class_name
        self.category = category
        self.states = states
        self.prefab_name = prefab_name
        self.bounding_box = bounding_box

    @staticmethod
    def from_dict(d):
        return GraphNode(d['id'], d['class_name'], d['category'], [State[s.upper()] for s in d['states']],
                         d['prefab_name'], Bounds(**d['bounding_box']))


class GraphEdge(object):
    def __init__(self, from_node: GraphNode, to_node: GraphNode, relation: GraphNode):
        self.from_node = from_node
        self.to_node = to_node
        self.relation = relation

    @staticmethod
    def from_dict(d):
        return GraphEdge(d['from_id'], d['to_id'], Relation[d['relation'].upper()])


class EnvironmentGraph(object):
    def __init__(self, nodes: Collection[GraphNode], edges: Collection[GraphEdge]):
        """
        :param nodes: list of GraphNode objects
        :param edges: list of GraphEdge
        """
        self._nodes = nodes
        self._edges = edges

    def from_node(self, node: GraphNode):
        """
        :param node: graph node
        :return: list of pairs (node2, relation) where (node, relation, node2) is an edge
        """
        pass # TODO: implement from_node

    def to_node(self, node: GraphNode):
        """
        :param node: graph node
        :return: list of pairs (node2, relation) where (node2, relation, node) is an edge
        """
        pass # TODO: implement to_node

    def find_edges(self, from_class, from_id, relation, to_class, to_id):
        pass

    def find_nodes(self, condition):
        pass

    @staticmethod
    def from_dict(d):
        nodes = [GraphNode.from_dict(n) for n in d['nodes']]
        edges = [GraphEdge.from_dict(e) for e in d['edges']]
        return EnvironmentGraph(nodes, edges)


class EnvironmentState(object):

    def __init__(self, graph: EnvironmentGraph):
        self._graph = graph
        self._script_objects = {}  # (name, instance) -> node id

    def evaluate(self, lvalue: 'LogicalValue'):
        return lvalue.evaluate(self)

    def select_nodes(self, obj: ScriptObject):
        """Enumerate nodes satisfying a script object. If object was already
        discovered, return node
        :param obj:
        :return:
        """
        node_id = self._script_objects.get((obj.name, obj.instance), None)
        if node_id is not None:
            return self.get_node_by_id(node_id)
        else:
            self.get_node()

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
        nodes = state.all_nodes()
        for n in nodes:
            yield n


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
        nodes = state.nodes_from(self.from_node, self.relation)
        for n in nodes:
            yield n


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
        return self.node_state in self.node.states


class NodeProperty(LogicalValue):

    def __init__(self, node: Node, node_property: Property):
        self.node = node
        self.node_property = node_property

    def evaluate(self, state: EnvironmentState):
        return state.check_node_property(self.node, self.node_property)


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


