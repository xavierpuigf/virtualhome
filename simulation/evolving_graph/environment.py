from enum import Enum
from abc import abstractmethod
from typing import List
import sys
import os
import copy
from .common import TimeMeasurement
from .scripts import ScriptObject

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
    SITTING = 5
    DIRTY = 6
    CLEAN = 7
    LYING = 8
    PLUGGED_IN = 9
    PLUGGED_OUT = 10


class Relation(Enum):
    ON = 1
    INSIDE = 2
    BETWEEN = 3
    CLOSE = 4
    FACING = 5
    HOLDS_RH = 6
    HOLDS_LH = 7
    SITTING = 8

    @classmethod
    def all(cls):
        return list(Relation)


class Property(Enum):
    SURFACES = 1
    GRABBABLE = 2
    SITTABLE = 3
    LIEABLE = 4
    HANGABLE = 5
    DRINKABLE = 6
    EATABLE = 7
    RECIPIENT = 8
    CUTTABLE = 9
    POURABLE = 10
    CAN_OPEN = 11
    HAS_SWITCH = 12
    READABLE = 13
    LOOKABLE = 14
    CONTAINERS = 15
    CLOTHES = 16
    PERSON = 17
    BODY_PART = 18
    COVER_OBJECT = 19
    HAS_PLUG = 20
    HAS_PAPER = 21
    MOVABLE = 22
    CREAM = 23


class Room(Enum):
    HOME_OFFICE = 1
    KITCHEN = 2
    LIVING_ROOM = 3
    BATHROOM = 4
    DINING_ROOM = 5
    BEDROOM = 6
    KIDS_BEDROOM = 7
    ENTRANCE_HALL = 8

    @classmethod
    def has_value(cls, value):
        return value.lower().replace(' ', '_') in [item.name.lower() for item in cls]

# EnvironmentGraph, nodes, edges and related structures
###############################################################################


class Bounds(object):
    def __init__(self, center, size):
        self.center = center
        self.size = size

    def to_dict(self):
        return {'center': self.center, 'size': self.size}


class Node(object):
    def __init__(self, id):
        self.id = id


class GraphNode(Node):

    def __init__(self, id, class_name, properties, states, category, prefab_name, bounding_box):
        super().__init__(id)
        self.class_name = class_name
        self.category = category
        self.properties = properties
        self.states = states
        self.prefab_name = prefab_name
        self.bounding_box = bounding_box

    def copy(self):
        return GraphNode(self.id, self.class_name, self.properties.copy(), self.states.copy(),
                         self.category, self.prefab_name, self.bounding_box)

    def __str__(self):
        return '<{}> ({})'.format(self.class_name, self.id)

    def to_dict(self):
        return {'id': self.id,
                'class_name': self.class_name,
                'category': self.category,
                'properties': [p.name for p in self.properties],
                'states': [s.name for s in self.states],
                'prefab_name': self.prefab_name,
                'bounding_box': None if self.bounding_box is None else self.bounding_box.to_dict()
                }

    @staticmethod
    def from_dict(d):
        kwargs = {
            "category": None, 
            "prefab_name": None, 
            "bounding_box": None
        }
        for k in kwargs.keys():
            if k in d:
                if k == 'bounding_box':
                    kwargs[k] = Bounds(**d[k]) if d[k] is not None else d[k]
                else:
                    kwargs[k] = d[k]

        return GraphNode(d['id'], d['class_name'], 
                         {s if isinstance(s, Property) else Property[s.upper()] for s in d['properties']},
                         {State[s.upper()] for s in d['states']},
                         **kwargs)


class GraphEdge(object):
    def __init__(self, from_node: GraphNode, relation: Relation, to_node: GraphNode):
        self.from_node = from_node
        self.relation = relation
        self.to_node = to_node


class NodeQueryType(Enum):
    ANY_NODE = 1
    NODE_WITH_ID = 2
    NODE_WITH_ATTR = 3


def _ensure_unique_nodes_unique_edges(graph_dict):
    
    nodes = graph_dict["nodes"]
    edges = graph_dict["edges"]
    
    new_nodes = {node["id"]: node for node in nodes}
    new_nodes = list(new_nodes.values())

    new_edges = {"{}.{}.{}".format(edge["from_id"], edge["relation_type"], edge["to_id"]): edge for edge in edges}
    new_edges = list(new_edges.values())
    
    return {"nodes": new_nodes, "edges": new_edges}

        
class EnvironmentGraph(object):

    def __init__(self, dictionary=None):
        self._max_node_id = 0
        self._edge_map = {}
        self._node_map = {}
        self._class_name_map = {}
        if dictionary is not None:
            dictionary = _ensure_unique_nodes_unique_edges(dictionary)
            self._from_dictionary(dictionary)
        else:
            self._dictionary = dictionary

    def _from_dictionary(self, d):
        nodes = [GraphNode.from_dict(n) for n in d['nodes']]
        for n in nodes:
            self._node_map[n.id] = n
            self._class_name_map.setdefault(n.class_name, []).append(n)
            if n.id > self._max_node_id:
                self._max_node_id = n.id
        edges = [(ed['from_id'], Relation[ed['relation_type'].upper()], ed['to_id'])
                 for ed in d['edges']]
        for from_id, relation, to_id in edges:
            es = self._edge_map.setdefault((from_id, relation), {})
            es[to_id] = self._node_map[to_id]

    def get_nodes(self):
        return self._node_map.values()

    def get_node_ids(self):
        return  self._node_map.keys()

    def get_node_map(self):
        return self._node_map

    def get_nodes_by_attr(self, attr: str, value):
        if attr == 'class_name':
            for node in self._class_name_map.get(value, []):
                yield node
        else:
            for node in self._node_map.values():
                if getattr(node, attr) == value:
                    yield node

    def get_char_node(self, char_index: int):
        chars = self._class_name_map.get('character', [])
        chars.sort(key=lambda node : node.id)
        assert char_index < len(chars), 'Character Index Out of bound! #chars is {}, char index is {}'.format(len(chars), char_index)
        yield chars[char_index]
        

    def get_node(self, node_id: int):
        return self._node_map.get(node_id, None)

    def get_nodes_from(self, from_node: Node, relation: Relation):
        return self._get_node_maps_from(from_node.id, relation).values()

    def get_node_ids_from(self, from_id: int, relation: Relation):
        return self._get_node_maps_from(from_id, relation).keys()

    def _get_node_maps_from(self, from_id: int, relation: Relation):
        return self._edge_map.get((from_id, relation), {})

    def get_from_pairs(self):
        return self._edge_map.keys()

    def get_max_node_id(self):
        return self._max_node_id

    def has_edge(self, from_node: Node, relation: Relation, to_node: Node):
        return to_node.id in self._get_node_maps_from(from_node.id, relation)

    def add_node(self, node: GraphNode):
        assert node.id not in self._node_map
        self._node_map[node.id] = node
        self._class_name_map.setdefault(node.class_name, []).append(node)
        if node.id > self._max_node_id:
            self._max_node_id = node.id

    def add_edge(self, from_node: Node, r: Relation, to_node: Node):
        assert from_node.id in self._node_map and to_node.id in self._node_map
        es = self._edge_map.setdefault((from_node.id, r), {})
        es[to_node.id] = to_node


# EnvironmentState
###############################################################################


class EnvironmentState(object):

    def __init__(self, graph: EnvironmentGraph, name_equivalence, instance_selection: bool=False):
        self.instance_selection = instance_selection
        self.executor_data = {}
        self._graph = graph
        self._name_equivalence = name_equivalence
        self._script_objects = {}  # (name, instance) -> node id
        self._new_nodes = {}  # map: node id -> GraphNode
        self._max_node_id = graph.get_max_node_id()
        self._removed_edges_from = {}  # map: (from_node id, relation) -> to_node id set
        self._new_edges_from = {}  # map: (from_node id, relation) -> to_node id set

    def evaluate(self, lvalue: 'LogicalValue'):
        return lvalue.evaluate(self)

    def select_nodes(self, obj: ScriptObject):
        if self.instance_selection:
            return [self.get_node(obj.instance)]
        else:
            """Enumerate nodes satisfying script object condition. If object was already
            discovered, return node
            """
            node_id = self._script_objects.get((obj.name, obj.instance), None)
            if node_id is not None:
                return [self.get_node(node_id)]
            else:
                nodes = []
                for name in [obj.name] + self._name_equivalence.get(obj.name, []):
                    nodes.extend(self.get_nodes_by_attr('class_name', name))
                return nodes

    def get_script_node(self, name: str, instance: int):
        return self._script_objects.get((name, instance), None)

    def get_state_node(self, obj: ScriptObject):
        if self.instance_selection:
            return self.get_node(obj.instance)
        else:
            node_id = self._script_objects.get((obj.name, obj.instance), -1)
        return None if node_id < 0 else self.get_node(node_id)

    def has_edge(self, from_node: Node, relation: Relation, to_node: Node):
        if to_node.id in self._removed_edges_from.get((from_node.id, relation), set()):
            return False
        elif to_node.id in self._new_edges_from.get((from_node.id, relation), set()):
            return True
        else:
            return self._graph.has_edge(from_node, relation, to_node)

    def get_node(self, node_id: int):
        if node_id in self._new_nodes:
            return self._new_nodes[node_id]
        else:
            return self._graph.get_node(node_id)

    def get_nodes_from(self, from_node: Node, relation: Relation):
        id_set = self._new_edges_from.get((from_node.id, relation), set())
        id_set.update(self._graph.get_node_ids_from(from_node.id, relation))
        removed_ids = self._removed_edges_from.get((from_node.id, relation), set())
        id_set.difference_update(removed_ids)
        result = []
        for node_id in id_set:
            if node_id in self._new_nodes:
                result.append(self._new_nodes[node_id])
            else:
                result.append(self._graph.get_node(node_id))
        return result

    def get_node_ids_from(self, from_id: int, relation: Relation):
        id_set = self._new_edges_from.get((from_id, relation), set())
        id_set.update(self._graph.get_node_ids_from(from_id, relation))
        removed_ids = self._removed_edges_from.get((from_id, relation), set())
        id_set.difference_update(removed_ids)
        return id_set

    def get_nodes(self):
        result = list(self._new_nodes.values())
        for node in self._graph.get_nodes():
            if node.id not in self._new_nodes:
                result.append(node)
        return result

    def get_max_node_id(self):
        return self._max_node_id

    def get_nodes_by_attr(self, attr: str, value):
        result = []
        added_new = set()
        for node in self._graph.get_nodes_by_attr(attr, value):
            if node.id not in self._new_nodes:
                result.append(node)
            else:
                new_node = self._new_nodes[node.id]
                if getattr(new_node, attr) == value:
                    result.append(new_node)
                    added_new.add(new_node.id)
        for new_node_id, new_node in self._new_nodes.items():
            if new_node_id not in added_new and getattr(new_node, attr) == value:
                result.append(new_node)
        return result

    def get_char_node(self, char_index: int):
        return self._graph.get_char_node(char_index)

    def add_edge(self, from_node: Node, relation: Relation, to_node: Node):
        if (from_node.id, relation) in self._removed_edges_from:
            to_node_ids = self._removed_edges_from[(from_node.id, relation)]
            if to_node.id in to_node_ids:
                to_node_ids.remove(to_node.id)
                return
        if not self._graph.has_edge(from_node, relation, to_node):
            self._new_edges_from.setdefault((from_node.id, relation), set()).add(to_node.id)

    def delete_edge(self, from_node: Node, relation: Relation, to_node: Node):
        if self._graph.has_edge(from_node, relation, to_node):
            self._removed_edges_from.setdefault((from_node.id, relation), set()).add(to_node.id)
        elif (from_node.id, relation) in self._new_edges_from:
            to_node_ids = self._new_edges_from[(from_node.id, relation)]
            to_node_ids.discard(to_node.id)

    def change_node(self, node: Node):
        assert node.id in self._new_nodes or self._graph.get_node(node.id) is not None
        self._new_nodes[node.id] = node

    def add_node(self, node: Node):
        self._max_node_id += 1
        node.id = self._max_node_id
        self._new_nodes[node.id] = node

    def change_state(self, changers: List['StateChanger'], node: Node = None, obj: ScriptObject = None, in_place = False):

        new_state = EnvironmentState(self._graph, self._name_equivalence, self.instance_selection)
        if in_place:
            new_state._new_nodes = self._new_nodes
            new_state._removed_edges_from = self._removed_edges_from
            new_state._new_edges_from = self._new_edges_from
            new_state._script_objects = self._script_objects
            new_state.executor_data = self.executor_data
        else:
            new_state._new_nodes = copy.deepcopy(self._new_nodes)
            new_state._removed_edges_from = copy.deepcopy(self._removed_edges_from)
            new_state._new_edges_from = copy.deepcopy(self._new_edges_from)
            new_state._script_objects = copy.deepcopy(self._script_objects)
            new_state.executor_data = copy.deepcopy(self.executor_data)

        if obj is not None and node is not None:
            new_state._script_objects[(obj.name, obj.instance)] = node.id
        new_state.apply_changes(changers)

        return new_state

    def apply_changes(self, changers: List['StateChanger']):
        for changer in changers:
            changer.apply_changes(self)

    def to_dict(self):
        edges = []
        from_pairs = self._new_edges_from.keys() | self._graph.get_from_pairs()
        for from_n, r in from_pairs:
            for to_n in self.get_node_ids_from(from_n, r):
                edges.append({'from_id': from_n, 'relation_type': r.name, 'to_id': to_n})
        return {'nodes': [n.to_dict() for n in self.get_nodes()], 'edges': edges}


# NodeEnumerator-s
###############################################################################


class NodeEnumerator(object):

    @abstractmethod
    def enumerate(self, state: EnvironmentState, **kwargs):
        pass


class AnyNode(NodeEnumerator):

    def enumerate(self, state: EnvironmentState, **kwargs):
        return state.get_nodes()


class NodeInstance(NodeEnumerator):

    def __init__(self, node: Node):
        self.node = node

    def enumerate(self, state: EnvironmentState, **kwargs):
        yield state.get_node(self.node.id)


class NodeParam(NodeEnumerator):

    def enumerate(self, state: EnvironmentState, **kwargs):
        if 'node' not in kwargs:
            raise Exception('"node" param not set')
        yield kwargs['node']


class RelationFrom(NodeEnumerator):

    def __init__(self, from_node: Node, relation: Relation):
        self.from_node = from_node
        self.relation = relation

    def enumerate(self, state: EnvironmentState, **kwargs):
        return state.get_nodes_from(self.from_node, self.relation)


class CharacterNode(NodeEnumerator):

    def __init__(self, char_index: int):
        self.char_index = char_index

    def enumerate(self, state: EnvironmentState, **kwargs):
        return state.get_char_node(self.char_index)


class ClassNameNode(NodeEnumerator):

    def __init__(self, class_name: str):
        self.class_name = class_name

    def enumerate(self, state: EnvironmentState, **kwargs):
        return state.get_nodes_by_attr('class_name', self.class_name)

class ObjectInsideNode(NodeEnumerator):

    def __init__(self, node: Node):
        self.container_node = node

    def enumerate(self, state: EnvironmentState, **kwargs):
        for n in state.get_nodes():
            if state.evaluate(ExistsRelation(NodeInstance(n), Relation.INSIDE, NodeInstanceFilter(self.container_node))):
                 yield n

class ObjectOnNode(NodeEnumerator):

    def __init__(self, node: Node):
        self.surface_node = node

    def enumerate(self, state: EnvironmentState, **kwargs):
        for n in state.get_nodes():
            if state.evaluate(ExistsRelation(NodeInstance(n), Relation.ON, NodeInstanceFilter(self.surface_node))):
                 yield n


class BodyNode(NodeEnumerator):

    def enumerate(self, state: EnvironmentState, **kwargs):
        for n in state.get_nodes():
            if Property.BODY_PART in n.properties:
                yield n


class SurfaceObjectNode(NodeEnumerator):
    """Find the objects that support `node`
    """
    def __init__(self, node: Node):
        self.node = node

    def enumerate(self, state: EnvironmentState, **kwargs):
        for n in state.get_nodes_from(self.node, Relation.ON):
            yield n

class BoxObjectNode(NodeEnumerator):
    """Find the objects that contain `node`
    """
    def __init__(self, node: Node):
        self.node = node

    def enumerate(self, state: EnvironmentState, **kwargs):
        for n in state.get_nodes_from(self.node, Relation.INSIDE):
            if n.category != 'Rooms':
                yield n


class FilteredNodes(NodeEnumerator):

    def __init__(self, enumerator: NodeEnumerator, condition: 'LogicalValue'):
        self.enumerator = enumerator
        self.condition = condition

    def enumerate(self, state: EnvironmentState, **kwargs):
        for n in self.enumerator.enumerate(state):
            if self.condition.evaluate(n):
                yield n


# NodeFilter-s
###############################################################################


class NodeFilter(object):

    @abstractmethod
    def filter(self, node: Node):
        pass


class NodeInstanceFilter(NodeFilter):

    def __init__(self, node: Node):
        self.node = node

    def filter(self, node: Node):
        return node.id == self.node.id


class NodeConditionFilter(NodeFilter):

    def __init__(self, value: 'LogicalValue'):
        self.value = value

    def filter(self, node: Node):
        return self.value.evaluate(node)


class AnyNodeFilter(NodeFilter):

    def filter(self, node: Node):
        return True


# LogicalValue-s
###############################################################################


class LogicalValue(object):

    @abstractmethod
    def evaluate(self, param, **kwargs):
        pass


class Not(LogicalValue):

    def __init__(self, value1: LogicalValue):
        self.value1 = value1

    def evaluate(self, param, **kwargs):
        return not self.value1.evaluate(param, **kwargs)


class And(LogicalValue):

    def __init__(self, *args: LogicalValue):
        self.values = args

    def evaluate(self, param, **kwargs):
        for value in self.values:
            if not value.evaluate(param, **kwargs):
                return False
        return True


class Constant(LogicalValue):

    def __init__(self, value: bool):
        self.value = value

    def evaluate(self, param, **kwargs):
        return self.value


class ExistsRelation(LogicalValue):

    def __init__(self, from_nodes: NodeEnumerator, relation: Relation, to_nodes: NodeFilter):
        self.from_nodes = from_nodes
        self.relation = relation
        self.to_nodes = to_nodes

    def evaluate(self, state: EnvironmentState, **kwargs):
        for fn in self.from_nodes.enumerate(state, **kwargs):
            for tn in state.get_nodes_from(fn, self.relation):
                if self.to_nodes.filter(tn):
                    return True
        return False


class CountRelations(LogicalValue):
    def __init__(self, from_nodes: NodeEnumerator, relation: Relation, to_nodes: NodeFilter, min_value: int):
        """
        Evaluates to true if there are at least min_value edges satisfying the conditions
        """
        self.from_nodes = from_nodes
        self.relation = relation
        self.to_nodes = to_nodes
        self.min_value = min_value

    def evaluate(self, state: EnvironmentState, **kwargs):
        count = 0
        for fn in self.from_nodes.enumerate(state, **kwargs):
            for tn in state.get_nodes_from(fn, self.relation):
                if self.to_nodes.filter(tn):
                    count += 1
                    if count >= self.min_value:
                        return True
        return False


class ExistRelations(LogicalValue):

    def __init__(self, from_nodes: NodeEnumerator, rf_pairs):
        self.from_nodes = from_nodes
        self.rf_pairs = rf_pairs

    def evaluate(self, state: EnvironmentState, **kwargs):
        for fn in self.from_nodes.enumerate(state, **kwargs):
            node_ok = True
            for (relation, node_filter) in self.rf_pairs:
                filter_ok = False
                for tn in state.get_nodes_from(fn, relation):
                    if node_filter.filter(tn):
                        filter_ok = True
                        break
                if not filter_ok:
                    node_ok = False
                    break
            if node_ok:
                return True
        return False


class IsRoomNode(LogicalValue):

    def __init__(self, room_name: str=None):
        self.room_name = room_name

    def evaluate(self, node: GraphNode, **kwargs):
        return node.category == 'Rooms' and (self.room_name is None or node.class_name == self.room_name)


class NodeAttrEq(LogicalValue):

    def __init__(self, attr: str, value):
        self.attr = attr
        self.value = value

    def evaluate(self, node: GraphNode, **kwargs):
        return self.value == getattr(node, self.attr)


class NodeAttrIn(LogicalValue):

    def __init__(self, value, attr: str):
        self.value = value
        self.attr = attr

    def evaluate(self, node: GraphNode, **kwargs):
        return self.value in getattr(node, self.attr)


class NodeClassNameEq(LogicalValue):

    def __init__(self, class_name: str):
        self.class_name = class_name

    def evaluate(self, node: GraphNode, **kwargs):
        return self.class_name == node.class_name


# StateChanger-s
###############################################################################


class StateChanger(object):

    @abstractmethod
    def apply_changes(self, state: EnvironmentState, **kwargs):
        pass


class AddEdges(StateChanger):

    def __init__(self, from_node: NodeEnumerator, relation: Relation, to_node: NodeEnumerator, add_reverse=False):
        self.from_node = from_node
        self.relation = relation
        self.to_node = to_node
        self.add_reverse = add_reverse

    def apply_changes(self, state: EnvironmentState, **kwargs):
        tm = TimeMeasurement.start('AddEdges')
        for n1 in self.from_node.enumerate(state):
            for n2 in self.to_node.enumerate(state):
                state.add_edge(n1, self.relation, n2)
                if self.add_reverse:
                    state.add_edge(n2, self.relation, n1)
        TimeMeasurement.stop(tm)


class DeleteEdges(StateChanger):

    def __init__(self, from_node: NodeEnumerator, relations, to_node: NodeEnumerator, delete_reverse=False):
        self.from_node = from_node
        self.relations = relations
        self.to_node = to_node
        self.delete_reverse = delete_reverse

    def apply_changes(self, state: EnvironmentState, **kwargs):
        tm = TimeMeasurement.start('DeleteEdges')
        for n1 in self.from_node.enumerate(state):
            for e in self.relations:
                for n2 in self.to_node.enumerate(state):
                    state.delete_edge(n1, e, n2)
                    if self.delete_reverse:
                        state.delete_edge(n2, e, n1)
        TimeMeasurement.stop(tm)


class ChangeNode(StateChanger):

    def __init__(self, node: GraphNode):
        self.node = node

    def apply_changes(self, state: EnvironmentState, **kwargs):
        state.change_node(self.node)


class AddNode(StateChanger):

    def __init__(self, node: GraphNode):
        self.node = node

    def apply_changes(self, state: EnvironmentState, **kwargs):
        state.add_node(self.node)


class ClearExecDataKey(StateChanger):

    def __init__(self, key):
        self.key = key

    def apply_changes(self, state: EnvironmentState, **kwargs):
        state.executor_data.pop(self.key, None)


class AddExecDataValue(StateChanger):

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def apply_changes(self, state: EnvironmentState, **kwargs):
        state.executor_data[self.key] = self.value
