import random
import json
import re
import os
import copy
import numpy as np
from evolving_graph.environment import EnvironmentGraph, Property, Room
from evolving_graph.execution import SitExecutor, LieExecutor


random.seed(123)


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)

def load_graph_dict(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data

def load_name_equivalence(file_name='../../resources/class_name_equivalence.json'):
    abs_dir_path = os.path.dirname(os.path.abspath(__file__))
    file_name_all = os.path.join(abs_dir_path, file_name)
    with open(file_name_all, 'r') as f:
        return json.load(f)


def load_object_states(file_name='../../resources/object_states.json'):
    abs_dir_path = os.path.dirname(os.path.abspath(__file__))
    file_name_all = os.path.join(abs_dir_path, file_name)
    with open(file_name_all, 'r') as f:
        return json.load(f)

def load_object_placing(file_name='../../resources/object_script_placing.json'):
    abs_dir_path = os.path.dirname(os.path.abspath(__file__))
    file_name_all = os.path.join(abs_dir_path, file_name)
    with open(file_name_all, 'r') as f:
        return json.load(f)


def load_properties_data(file_name='../../resources/properties_data.json'):
    abs_dir_path = os.path.dirname(os.path.abspath(__file__))
    file_name_all = os.path.join(abs_dir_path, file_name)
    with open(file_name_all, 'r') as f:
        pd_dict = json.load(f)
        return {key: [Property[p] for p in props] for (key, props) in pd_dict.items()}


def build_unity2object_script(script_object2unity_object):
    """Builds mapping from Unity 2 Script objects. It works by creating connected
      components between objects: A: [c, d], B: [f, e]. Since they share
      one object, A, B, c, d, f, e should be merged
    """
    unity_object2script_object = {}
    object_script_merge = {}
    for k, vs in script_object2unity_object.items():
        vs = [x.lower().replace('_', '') for x in vs]
        kmod = k.lower().replace('_', '')
        object_script_merge[k] = [kmod] + vs
        if kmod in unity_object2script_object:
            prev_parent = unity_object2script_object[kmod]
            dest_parent = prev_parent
            source_parent = k
            if len(k) < len(prev_parent) and prev_parent != 'computer':
                dest_parent = k
                source_parent = prev_parent
            children_source = object_script_merge[source_parent]
            object_script_merge[dest_parent] += children_source
            for child in children_source: unity_object2script_object[child] = dest_parent

        else:
            unity_object2script_object[kmod] = k
        for v in vs:
            if v in unity_object2script_object:
                prev_parent = unity_object2script_object[v]
                dest_parent = prev_parent
                source_parent = k
                if len(k) < len(prev_parent) and prev_parent != 'computer':
                    dest_parent = k
                    source_parent = prev_parent
                children_source = object_script_merge[source_parent]
                object_script_merge[dest_parent] += children_source
                for child in children_source: unity_object2script_object[child] = dest_parent
            else:
                unity_object2script_object[v] = k

    return unity_object2script_object


class BinaryVariable(object):

    def __init__(self, v_list, default):

        assert default in v_list

        v1, v2 = v_list
        self.default = default
        if default == v1:
            self.negative = v2
            self.positive = v1
        else:
            self.positive = v2
            self.negative = v1

    def invert(self):
        if self.default == self.positive:
            self.default = self.negative
        else:
            self.default = self.positive

    def set_to_default_state(self, node):
        while self.negative in node["states"]:
            node["states"].remove(self.negative)
        if self.positive not in node["states"]:
            node["states"].append(self.positive)

    def sample_state(self, node):

        sampled_state = random.choice([self.positive, self.negative])
        self.set_node_state(node, sampled_state)
    
    def set_node_state(self, node, node_state):

        assert node_state in [self.positive, self.negative]
        if node_state == self.positive:
            remove_state = self.negative
        else:
            remove_state = self.positive
        
        while remove_state in node["states"]:
            node["states"].remove(remove_state)

        if node_state not in node["states"]:
            node["states"].append(node_state)

    def check(self, node, verbose):

        if self.positive not in node["states"] and self.negative not in node["states"]:
            if verbose:
                print("Neither {} nor {} in states".format(self.positive, self.negative), node)
            return False
        if not ((self.positive in node["states"] and self.negative not in node["states"]) or (self.positive not in node["states"] and self.negative in node["states"])):
            if verbose:
                print("Should exist at least on {}, {}".format(self.positive, self.negative), node)
            return False
        
        if self.positive in node["states"] and len([s for s in node["states"] if s == self.positive]) != 1:
            if verbose:
                print("Too many {} in states".format(self.positive))    
            self.set_node_state(node, self.positive)

        if self.negative in node["states"] and len([s for s in node["states"] if s == self.negative]) != 1:
            if verbose:
                print("Too many {} in states".format(self.negative))    
            self.set_node_state(node, self.negative)

        return True


class graph_dict_helper(object):

    def __init__(self, properties_data=None, object_placing=None, object_states=None, max_nodes=300):
        if properties_data is None:
            properties_data = load_properties_data()
        if object_placing is None:
            object_placing = load_object_placing()
        if object_states is None:
            object_states = load_object_states()

        self.properties_data = properties_data
        self.object_placing = object_placing
        self.object_states = object_states
        self.max_nodes = max_nodes

        self.open_closed = BinaryVariable(["OPEN", "CLOSED"], default="CLOSED")
        self.on_off = BinaryVariable(["ON", "OFF"], default="OFF")
        self.clean_dirty = BinaryVariable(["CLEAN", "DIRTY"], default="CLEAN")
        self.plugged_in_out = BinaryVariable(["PLUGGED_IN", "PLUGGED_OUT"], default="PLUGGED_IN")

        self.binary_variables = [self.open_closed, self.on_off, self.clean_dirty, self.plugged_in_out]

        self.body_part = ['face', 'leg', 'arm', 'eye', 'hand', 'feet']
        self.possible_rooms = ['home_office', 'kitchen', 'living_room', 'bathroom', 'dining_room', 'bedroom', 'kids_bedroom', 'entrance_hall']
        self.script_object2unity_object = load_name_equivalence()
        self.unity_object2script_object = build_unity2object_script(self.script_object2unity_object)
        self.equivalent_rooms = {
            "kitchen": "dining_room", 
            "dining_room": "kitchen", 
            "entrance_hall": "living_room", 
            "home_office": "living_room", 
            "living_room": "home_office",
            "kids_bedroom": "bedroom"
        }

        # precondition to simulator
        self.relation_script_precond_simulator = {
            "inside": "INSIDE", 
            "location": "INSIDE", 
            "atreach": "CLOSE", 
            "in": "ON"
        }

        self.states_script_precond_simulator = {
            "dirty": "DIRTY", 
            "clean": "CLEAN", 
            "open": "OPEN", 
            "closed": "CLOSED", 
            "plugged": "PLUGGED_IN", 
            "unplugged": "PLUGGED_OUT", 
            "is_on": "ON", 
            "is_off": "OFF", 
            "sitting": "SITTING", 
            "lying": "LYING"
        }

        # object_placing.json
        self.relation_placing_simulator = {
            "in": "INSIDE", 
            "on": "ON", 
            "nearby": "CLOSE"
        }

        # object_states.json
        self.states_mapping = {
            "dirty": "dirty", 
            "clean": "clean", 
            "open": "open", 
            "closed": "closed", 
            "plugged": "plugged_in", 
            "unplugged": "plugged_out", 
            "on": "on", 
            "off": "off"
        }

    def initialize(self, graph_dict):
        script_object_ids = [node["id"] for node in filter(lambda v: v["id"] >= 1000 and v["id"] < 2000, graph_dict["nodes"])]
        random_object_ids = [node["id"] for node in filter(lambda v: v["id"] >= 2000, graph_dict["nodes"])]

        self.script_objects_id = max(script_object_ids) if len(script_object_ids) != 0 else 1000
        self.random_objects_id = max(random_object_ids) if len(random_object_ids) != 0 else 2000

    def check_binary(self, graph_dict, id_checker, verbose):
        
        open_closed = self.open_closed
        on_off = self.on_off
        plugged_in_out = self.plugged_in_out
        for node in graph_dict["nodes"]:

            if id_checker(node["id"]):
                # always set to off, closed, open, clean
                if "CAN_OPEN" in node["properties"]:
                    if not open_closed.check(node, verbose):
                        open_closed.set_to_default_state(node)
                        
                if "HAS_PLUG" in node["properties"]:
                    if not plugged_in_out.check(node, verbose):
                        plugged_in_out.set_to_default_state(node)

                if "HAS_SWTICH" in node["properties"]:
                    if not on_off.check(node, verbose):
                        on_off.set_to_default_state(node)

                if "light" in node["class_name"] or "lamp" in node["class_name"]:
                    if not on_off.check(node, verbose):
                        on_off.set_node_state(node, "ON")

                if node["category"] == "Doors":
                    if not open_closed.check(node, verbose):
                        open_closed.set_node_state(node, "OPEN")


    def open_all_doors(self, graph_dict):

        open_closed = self.open_closed
        for node in graph_dict["nodes"]:
            if node["category"] == "Doors":
                open_closed.set_node_state(node, "OPEN")
    
    def get_object_binary_variables(self, object_name):
        '''
        For a given object name, obtains the binary variables
        '''
        states = self.object_states[object_name]
        bin_vars = self.get_binary_variables(states)
        return bin_vars

    def get_binary_variables(self, possible_states):
        '''
        Given a set of possible_states, returns the binary_variables associated
        '''
        added_variables = []
        state_to_bin_var = {}
        possible_states = []
        for bin_var in self.binary_variables:
            state_to_bin_var[bin_var.positive] = (bin_var, bin_var.default)
            state_to_bin_var[bin_var.negative] = (bin_var, bin_var.default)

        for state in possible_states:
            bin_var, default_var = state_to_bin_var[state]
            if default_var not in added_variables:
                added_variables.append(default_var)
                possible_states.append(bin_var)

        return possible_states
            
                
    def set_to_default_state(self, graph_dict, first_room, id_checker):
        
        open_closed = self.open_closed
        on_off = self.on_off
        clean_dirty = self.clean_dirty
        plugged_in_out = self.plugged_in_out
        body_part = self.body_part

        character_id = [i["id"] for i in filter(lambda v: v["class_name"] == 'character', graph_dict["nodes"])][0]

        for node in graph_dict["nodes"]:

            if id_checker(node["id"]):
                # always set to off, closed, open, clean
                if "CAN_OPEN" in node["properties"]:
                    open_closed.set_to_default_state(node)
                    if node["class_name"] == "door":
                        open_closed.set_node_state(node, "OPEN")
                if "HAS_PLUG" in node["properties"]:
                    plugged_in_out.set_to_default_state(node)
                if "HAS_SWTICH" in node["properties"]:
                    on_off.set_to_default_state(node)
                clean_dirty.set_to_default_state(node)

                if node["class_name"] == 'character' and first_room is not None:
                    # character is not sitting, lying, holding, not close to anything
                    graph_dict["edges"] = [e for e in filter(lambda e: e["from_id"] != character_id and e["to_id"] != character_id, graph_dict["edges"])]

                    # set the character inside the pre-specified room
                    first_room_id = [i["id"] for i in filter(lambda v: v['class_name'] == first_room, graph_dict["nodes"])][0]
                    graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": character_id, "to_id": first_room_id})
                    node["states"] = []

                if "light" in node["class_name"] or "lamp" in node["class_name"]:
                    on_off.set_node_state(node, "ON")

                if node["category"] == "Doors":
                    open_closed.set_node_state(node, "OPEN")

                if any([Property.BODY_PART in node["properties"] for v in body_part]):
                    graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": character_id, "to_id": node["id"]})
                    graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": node["id"], "to_id": character_id})
     
    def _add_missing_node(self, graph_dict, id, obj, category):
                    
            graph_dict['nodes'].append({
                "properties": [i.name for i in self.properties_data[obj]], 
                "id": id, 
                "states": [], 
                "category": category, 
                "class_name": obj
            })

    def _random_pick_a_room_with_objects_name_in_graph(self, available_rooms_in_graph, available_rooms_in_graph_id, objects_in_script, available_nodes, graph_dict):

        # Room is not specified in this program, assign one to it
        hist = np.zeros(len(available_rooms_in_graph_id))
        for obj in objects_in_script:
            obj_name = obj[0]
            if obj_name == 'character':
                continue
            for node in available_nodes:
                if node['class_name'] == obj_name:
                    edges = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] in available_rooms_in_graph_id, graph_dict["edges"])]
                        
                    if len(edges) > 0:
                        for edge in edges:
                            dest_id = edge['to_id']
                            idx = available_rooms_in_graph_id.index(dest_id)
                            hist[idx] += 1

        if hist.std() < 1e-5:
            room_name = random.choice(available_rooms_in_graph)
        else:
            idx = np.argmax(hist)
            room_name = available_rooms_in_graph[idx]

        return room_name

    def _any_room_except(self, first_room, available_rooms_in_graph):
        available_rooms = copy.deepcopy(available_rooms_in_graph)
        available_rooms.remove(first_room)
        return random.choice(available_rooms)

    def modify_script_with_specified_id(self, script, id_mapping, room_mapping):

        # change the id in script
        for script_line in script:
            for parameter in script_line.parameters:
                if parameter.name in self.possible_rooms:
                    parameter.name = room_mapping[parameter.name]
                try:
                    assert (parameter.name, parameter.instance) in id_mapping
                except:
                    print(parameter.name, parameter.instance)
                    print(id_mapping)
                    assert (parameter.name, parameter.instance) in id_mapping

                parameter.instance = id_mapping[(parameter.name, parameter.instance)]

    def ensure_light_on(self, graph_dict, id_checker):

        on_off = self.on_off
        for node in graph_dict["nodes"]:
            if 'light' in node["class_name"] or 'lamp' in node["class_name"]:
                if id_checker(node["id"]):
                    if "ON" not in node["states"]:
                        while "OFF" in node["states"]:
                            node["states"].remove("OFF")
                        on_off.set_node_state(node, "ON")

    def add_missing_object_from_script(self, script, precond, graph_dict, id_mapping):

        equivalent_rooms = self.equivalent_rooms
        possible_rooms = self.possible_rooms

        available_rooms_in_graph = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]
        available_rooms_in_graph_id = [i['id'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]

        available_nodes = copy.deepcopy(graph_dict['nodes'])
        available_name = list(set([node['class_name'] for node in available_nodes]))

        # create room mapping
        room_mapping = {}
        for room in possible_rooms:
            nroom = room
            rooms_tried = []
            while nroom not in available_rooms_in_graph and nroom not in rooms_tried:
                rooms_tried.append(nroom)
                assert nroom in equivalent_rooms, "Not pre-specified mapping for room: {}".format(nroom)
                nroom = equivalent_rooms[nroom]    
            assert nroom in available_rooms_in_graph, "No equivalent room in graph for room: {}".format(nroom)
            room_mapping[room] = nroom
        
        # use room mapping to change the precond (in-place opetation)
        for precond_i in precond:
            if 'location' in precond_i:
                room = precond_i['location'][1][0] 
                precond_i['location'][1][0] = room_mapping[room]
        
        # apply room mapping to the script
        for script_line in script:
            for parameter in script_line.parameters:
                if parameter.name in possible_rooms:
                    parameter.name = room_mapping[parameter.name]

        # find the first room
        first_room = None
        for script_line in script:
            for parameter in script_line.parameters:
                if parameter.name in possible_rooms and first_room is None:
                    first_room = parameter.name

        # initialize the `objects_in_script`
        objects_in_script = {}
        character_id = [i for i in filter(lambda v: v['class_name'] == 'character', graph_dict["nodes"])][0]["id"]
        key = ('character', 1)
        objects_in_script[key] = id_mapping[key] if key in id_mapping else character_id

        for key in script.obtain_objects():
            if key not in objects_in_script:
                objects_in_script[key] = id_mapping[key] if key in id_mapping else None

        # set up the first room
        #location_precond = {tuple(i['location'][0]): i['location'][1][0] for i in filter(lambda v: 'location' in v, precond)}
        location_precond = {(i['location'][0][0], int(i['location'][0][1])): i['location'][1][0] for i in filter(lambda v: 'location' in v, precond)}
        rooms_in_precond = list(set([i for i in location_precond.values()]))
        if first_room == None:
            assert len(rooms_in_precond) == 0
            first_room = self._random_pick_a_room_with_objects_name_in_graph(available_rooms_in_graph, available_rooms_in_graph_id, objects_in_script, available_nodes, graph_dict)
        else:
            first_room = self._any_room_except(first_room, available_rooms_in_graph)
        assert first_room is not None and first_room in available_rooms_in_graph

        # mapping objects
        for obj in objects_in_script.keys():
            # objects that are specified already
            if objects_in_script[obj] is not None:
                continue

            room_obj = location_precond[obj] if obj in location_precond else first_room
            room_id = [i["id"] for i in filter(lambda v: v['class_name'] == room_obj, graph_dict["nodes"])][0]

            if obj[0] in possible_rooms:
                id_to_be_assigned = [i["id"] for i in filter(lambda v: v["class_name"] == obj[0], graph_dict["nodes"])]
                objects_in_script[obj] = id_to_be_assigned[0]
            elif obj[0] in available_name:
                added = False
                possible_matched_nodes = [i for i in filter(lambda v: v['class_name'] == obj[0], available_nodes)]
                # existing nodes
                for node in possible_matched_nodes:
                    obj_in_room = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v["to_id"] == room_id, graph_dict["edges"])]
                    if len(obj_in_room) == 0:
                        continue
                    else:
                        objects_in_script[obj] = node['id']
                        available_nodes.remove(node)
                        added = True
                        break

                if not added:
                    # add node
                    node_with_same_class_name = [node for node in filter(lambda v: v["class_name"] == obj[0], graph_dict["nodes"])]
                    category = node_with_same_class_name[0]['category']
                    self._add_missing_node(graph_dict, self.script_objects_id, obj[0], category)
                    objects_in_script[obj] = self.script_objects_id
                    # add edges
                    graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": self.script_objects_id, "to_id": room_id})
                    self.script_objects_id += 1
            else:
                # add missing nodes
                self._add_missing_node(graph_dict, self.script_objects_id, obj[0], 'placable_objects')
                objects_in_script[obj] = self.script_objects_id
                # add edges
                graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": self.script_objects_id, "to_id": room_id})
                self.script_objects_id += 1


        # change the id in script
        for script_line in script:
            for parameter in script_line.parameters:
                parameter.instance = objects_in_script[(parameter.name, parameter.instance)]
                
        return objects_in_script, first_room, room_mapping

    def prepare_from_precondition(self, precond, objects_in_script, graph_dict):

        object_placing = self.object_placing
        objects_to_place = list(object_placing.keys())

        relation_script_precond_simulator = self.relation_script_precond_simulator
        states_script_precond_simulator = self.states_script_precond_simulator
        open_closed = self.open_closed
        on_off = self.on_off
        clean_dirty = self.clean_dirty
        plugged_in_out = self.plugged_in_out

        for p in precond:
            for k, v in p.items():
                if k == 'location':
                    # handle when adding missing scripts
                    continue
                if k in relation_script_precond_simulator:
                    src_name, src_id = v[0]
                    tgt_name, tgt_id = v[1]
                    src_id = int(src_id)
                    tgt_id = int(tgt_id)

                    src_id = objects_in_script[(src_name.lower().replace(' ', '_'), src_id)]
                    tgt_id = objects_in_script[(tgt_name.lower().replace(' ', '_'), tgt_id)]

                    graph_dict['edges'].append({'relation_type': relation_script_precond_simulator[k], 'from_id': src_id, 'to_id': tgt_id})
                    if k == 'atreach':
                        graph_dict['edges'].append({'relation_type': relation_script_precond_simulator[k], 'from_id': tgt_id, 'to_id': src_id})
                elif k in states_script_precond_simulator:
                    obj_id = objects_in_script[(v[0].lower().replace(' ', '_'), int(v[1]))]
                    for node in graph_dict['nodes']:
                        if node['id'] == obj_id:
                            if k in ['is_on', 'is_off']:
                                on_off.set_node_state(node, states_script_precond_simulator[k])
                            elif k in ['open', 'closed']:
                                open_closed.set_node_state(node, states_script_precond_simulator[k])
                            elif k in ['dirty', 'clean']:
                                clean_dirty.set_node_state(node, states_script_precond_simulator[k])
                            elif k in ['plugged', 'unplugged']:
                                plugged_in_out.set_node_state(node, states_script_precond_simulator[k])
                            elif k == 'sitting':
                                if "SITTING" not in node["states"]: node["states"].append("SITTING")
                            elif k == 'lying':
                                if "LYING" not in node["states"]: node["states"].append("LYING")
                            break
                elif k in ["occupied", "free"]:
                    obj_id = objects_in_script[(v[0].lower().replace(' ', '_'), int(v[1]))]
                    for node in graph_dict['nodes']:
                        if node['id'] == obj_id:
                            if k == 'free':
                                self._change_to_totally_free(node, graph_dict)
                            elif k == 'occupied':
                                self._change_to_occupied(node, graph_dict, objects_to_place)
                            break
    
    def merge_object_name(self, object_name):
        if object_name in self.script_object2unity_object:
            unity_name = self.script_object2unity_object[object_name][0].replace('_', '')
        else:
            unity_name = object_name.replace('_', '')
        if unity_name not in self.unity_object2script_object:
            return object_name
        return self.unity_object2script_object[unity_name]

    def add_random_objs_graph_dict(self, graph_dict, n):

        object_placing = self.object_placing
        relation_placing_simulator = self.relation_placing_simulator

        objects_to_place = list(object_placing.keys())
        random.shuffle(objects_to_place)
        rooms_id = [node["id"] for node in filter(lambda v: v['class_name'] in self.possible_rooms, graph_dict["nodes"])]

        def _add_node(src_name, tgt_node, tgt_name):
            tgt_id = tgt_node["id"]
            self._add_missing_node(graph_dict, self.random_objects_id, src_name, "placable_objects")
            specified_room_id = [edge["to_id"] for edge in filter(lambda v: v["from_id"] == tgt_id and v["relation_type"] == "INSIDE" and v["to_id"] in rooms_id, graph_dict["edges"])][0]
            graph_dict["edges"].append({'relation_type': "INSIDE", "from_id": self.random_objects_id, "to_id": specified_room_id})
            graph_dict["edges"].append({'relation_type': relation_placing_simulator[tgt_name["relation"].lower()], "from_id": self.random_objects_id, "to_id": tgt_id})
            graph_dict["edges"].append({'relation_type': "CLOSE", "from_id": self.random_objects_id, "to_id": tgt_id})
            graph_dict["edges"].append({'relation_type': "CLOSE", "from_id": tgt_id, "to_id": self.random_objects_id})
            self.random_objects_id += 1
            
        while n > 0:

            src_name = random.choice(objects_to_place)
            tgt_names = copy.deepcopy(object_placing[src_name])
            # Merge object names
            src_name = self.merge_object_name(src_name)
            for tgt_name in tgt_names:
                tgt_name['destination'] = self.merge_object_name(tgt_name['destination']) 
            random.shuffle(tgt_names)
            for tgt_name in tgt_names:
                tgt_nodes = [i for i in filter(lambda v: v["class_name"] == tgt_name['destination'], graph_dict["nodes"])]
                if len(tgt_nodes) != 0:

                    max_occupancies = max(SitExecutor._MAX_OCCUPANCIES.get(tgt_name['destination'], 0), LieExecutor._MAX_OCCUPANCIES.get(tgt_name['destination'], 0))
                    if max_occupancies == 0:
                        tgt_node = random.choice(tgt_nodes)
                        _add_node(src_name, tgt_node, tgt_name)
                        n -= 1
                        break
                    else:
                        # find node with available space
                        free_tgt_nodes = []
                        for tgt_node in tgt_nodes:
                            occupied_edges = [_edge for _edge in filter(lambda v: v["relation_type"] == "ON" and v["to_id"] == tgt_node["id"] , graph_dict["edges"])]
                            if len(occupied_edges) < max_occupancies:
                                free_tgt_nodes.append(tgt_node)

                        if len(free_tgt_nodes) != 0:
                            tgt_node = random.choice(free_tgt_nodes)
                            _add_node(src_name, tgt_node, tgt_name)
                            n -= 1
                            break

    def random_change_object_state(self, objects_in_script, graph_dict, id_checker):

        open_closed = self.open_closed
        on_off = self.on_off
        clean_dirty = self.clean_dirty
        plugged_in_out = self.plugged_in_out
        object_states = self.object_states
        states_mapping = self.states_mapping

        available_states = ['dirty', 'clean', 'open', 'closed', 'free', 'occupied', 'plugged', 'unplugged', 'on', 'off']
        for node in graph_dict["nodes"]:
            if id_checker(node["id"]):
                if node["class_name"] in object_states:
                    possible_states = object_states[node["class_name"]]
                    possible_states = [i for i in filter(lambda v: v in available_states, possible_states)]
                    if len(possible_states) == 0:
                        continue

                    state = random.choice(possible_states)
                    if state in ['free', 'occupied']:
                        # implemeted with `add_random_objs_graph_dict`
                        pass
                    else:
                        state = states_mapping[state]
                        if state in ['dirty', 'clean']:
                            clean_dirty.sample_state(node)
                        elif state in ['on', 'off']:
                            on_off.sample_state(node)
                        elif state in ['open', 'closed']:
                            open_closed.sample_state(node)
                        elif state in ['plugged_in', 'plugged_out']:
                            plugged_in_out.sample_state(node)

    def _remove_one_random_nodes(self, graph_dict):
        start_id = 2000
        random_nodes_ids = [node["id"] for node in filter(lambda v: v["id"] >= start_id, graph_dict["nodes"])]
        
        if len(random_nodes_ids) != 0:
            remove_id = np.min(random_nodes_ids)
            graph_dict["nodes"] = [node for node in filter(lambda v: v["id"] != remove_id, graph_dict["nodes"])]
            graph_dict["edges"] = [edge for edge in filter(lambda v: v["from_id"] != remove_id and v["to_id"] != remove_id, graph_dict["edges"])]

    def _change_to_occupied(self, node, graph_dict, objects_to_place):

        if node["class_name"] in SitExecutor._MAX_OCCUPANCIES or node["class_name"] in LieExecutor._MAX_OCCUPANCIES:
            name = node["class_name"]
            max_occupancy = SitExecutor._MAX_OCCUPANCIES[name] if name in SitExecutor._MAX_OCCUPANCIES else LieExecutor._MAX_OCCUPANCIES[name]
            occupied_edges = [_edge for _edge in filter(lambda v: v["relation_type"] == "ON" and v["to_id"] == node["id"] , graph_dict["edges"])]
            current_state = 'free' if len(occupied_edges) < max(max_occupancy-1, 1) else "occupied"

            if current_state != "occupied":
                rooms_id = [_node["id"] for _node in filter(lambda v: v["category"] == 'Rooms', graph_dict["nodes"])]
                room_id = None
                for edge in graph_dict["edges"]:
                    if edge["relation_type"] == "INSIDE" and edge["from_id"] == node["id"] and edge["to_id"] in rooms_id:
                        room_id = edge["to_id"]
                
                assert room_id is not None, print("{}({}) doesn't exist in any room".format(node["class_name"], node["id"]))

                number_objects_to_add = max_occupancy - len(occupied_edges)
                if number_objects_to_add < 0:
                    import ipdb
                    ipdb.set_trace()
                
                object_placing = self.object_placing
                random.shuffle(objects_to_place)

                for src_name in objects_to_place:
                    tgt_names = object_placing[src_name]
                    src_name = self.merge_object_name(src_name)
                    for tgt_name in tgt_names:
                        tgt_name['destination'] = self.merge_object_name(tgt_name['destination']) 
                    if name in [i["destination"] for i in filter(lambda v: v["relation"] == 'ON', tgt_names)]:
                        self._remove_one_random_nodes(graph_dict)
                        self._add_missing_node(graph_dict, self.random_objects_id, src_name, 'placable_objects')
                        
                        graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": self.random_objects_id, "to_id": room_id})
                        graph_dict["edges"].append({"relation_type": "ON", "from_id": self.random_objects_id, "to_id": node["id"]})
                        graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": self.random_objects_id, "to_id": node["id"]})
                        graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": node["id"], "to_id": self.random_objects_id})
                        self.random_objects_id += 1
                        number_objects_to_add -= 0
                        if number_objects_to_add <= 0:
                            break

    def _change_to_totally_free(self, node, graph_dict):

        if node["class_name"] in SitExecutor._MAX_OCCUPANCIES or node["class_name"] in LieExecutor._MAX_OCCUPANCIES:

            occupied_edges = [_edge for _edge in filter(lambda v: v["relation_type"] == "ON" and v["to_id"] == node["id"] , graph_dict["edges"])]

            occupied_nodes_id = [_edge["from_id"] for _edge in occupied_edges]
            removed_edges = []

            for occupied_node_id in occupied_nodes_id:
                removed_edges += [edge for edge in filter(lambda v: v["from_id"] == occupied_node_id and v["to_id"] == node["id"], graph_dict["edges"])]
                removed_edges += [edge for edge in filter(lambda v: v["from_id"] == node["id"] and v["to_id"] == occupied_node_id, graph_dict["edges"])]

            for edge in removed_edges:
                graph_dict["edges"].remove(edge)
                                    
            floor_id = [_node["id"] for _node in filter(lambda v: v["class_name"] == 'floor', graph_dict["nodes"])]
            for obj_id in occupied_nodes_id:
                to_id = random.choice(floor_id)
                graph_dict["edges"].append({"relation_type": "ON", "from_id": obj_id, "to_id": to_id})
                graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": obj_id, "to_id": to_id})
                graph_dict["edges"].append({"relation_type": "CLOSE", "from_id": to_id, "to_id": obj_id})

    def check_objs_in_room(self, graph_dict):

        rooms_id = [node["id"] for node in filter(lambda v: v["category"] == 'Rooms', graph_dict["nodes"])]
        other_id = [node["id"] for node in filter(lambda v: v["category"] != 'Rooms', graph_dict["nodes"])]
        id2name = {node["id"]: node["class_name"] for node in graph_dict["nodes"]}

        for id in other_id:
            in_room = []
            for edge in graph_dict["edges"]:
                if edge["from_id"] == id and edge["relation_type"] == "INSIDE" and edge["to_id"] in rooms_id:
                    in_room.append(edge["to_id"])
                    
            if len(in_room) > 1:
                print("src object: {}({})".format(id2name[id], id), "in_rooms:", ', '.join([id2name for i in in_room]))
                print("exist in more than one room")
            elif len(in_room) == 0:
                print("src object: {}({})".format(id2name[id], id))
