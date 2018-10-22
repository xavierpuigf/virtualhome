import random
import json
import re
import os
import copy
import numpy as np
from environment import EnvironmentGraph, Property, Room
from execution import SitExecutor
import ipdb

random.seed(123)


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)

def load_graph_dict(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data

def load_name_equivalence(file_name='resources/class_name_equivalence.json'):
    abs_dir_path = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(abs_dir_path, file_name)
    with open(file_name) as f:
        return json.load(f)


def load_object_placing(file_name='resources/object_placing.json'):
    with open(file_name) as f:
        return json.load(f)


def load_properties_data(file_name='resources/properties_data.json'):
    with open(file_name) as f:
        pd_dict = json.load(f)
        return {key: [Property[p] for p in props] for (key, props) in pd_dict.items()}


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
        if self.negative in node["states"]:
            node["states"].remove(self.negative)
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
        
        if remove_state in node["states"]:
            node["states"].remove(remove_state)
        node["states"].append(node_state)


class graph_dict_helper(object):

    def __init__(self, properties_data, object_placing, object_states):
        self.properties_data = properties_data
        self.object_placing = object_placing
        self.object_states = object_states

        self.open_closed = BinaryVariable(["OPEN", "CLOSED"], default="CLOSED")
        self.on_off = BinaryVariable(["ON", "OFF"], default="OFF")
        self.clean_dirty = BinaryVariable(["CLEAN", "DIRTY"], default="CLEAN")
        self.plugged_in_out = BinaryVariable(["PLUGGED_IN", "PLUGGED_OUT"], default="PLUGGED_IN")

        self.body_part = ['face', 'leg', 'arm', 'eye', 'hand', 'feet']
        self.possible_rooms = ['home_office', 'kitchen', 'living_room', 'bathroom', 'dining_room', 'bedroom', 'kids_bedroom', 'entrance_hall']
        
        self.equivalent_rooms = {
            "kitchen": ["dining_room"], 
            "dining_room": ["kitchen"], 
            "entrance_hall": ["living_room"], 
            "home_office": ["living_room"], 
            "living_room": ["home_office"],
            "kids_bedroom": ["bedroom"]
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

    def initialize(self):
        self.script_objects_id = 1000
        self.random_objects_id = 2000

    def set_to_default_state(self, graph_dict, id_checker):
        
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
                if "HAS_PLUG" in node["properties"]:
                    plugged_in_out.set_to_default_state(node)
                if "HAS_SWTICH" in node["properties"]:
                    on_off.set_to_default_state(node)
                clean_dirty.set_to_default_state(node)

                # character is not sitting, lying, holding, not close to anything
                if node["class_name"] == 'character':
                    # character is not inside anything 
                    graph_dict["edges"] = [e for e in filter(lambda e: e["from_id"] != character_id and e["to_id"] != character_id, graph_dict["edges"])]

                    # set the character inside the pre-specified room
                    default_room_id = [i["id"] for i in filter(lambda v: v["class_name"] == 'living_room', graph_dict["nodes"])][0]
                    graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": character_id, "to_id": default_room_id})

                    node["states"] = []

                if "light" in node["class_name"]:
                    node["states"].append("ON")

                if node["category"] == "Doors":
                    node["states"].append("OPEN")

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

    def add_missing_object_from_script(self, script, graph_dict):
        
        available_rooms = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]
        available_rooms_id = [i['id'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]

        equivalent_rooms = self.equivalent_rooms
        possible_rooms = self.possible_rooms

        room_mapping = {}
        for room in possible_rooms:
            if room not in available_rooms:
                assert room in equivalent_rooms, "Not pre-specified mapping for room: {}".format(room)
                room_mapping[room] = random.choice(equivalent_rooms[room])


        character_id = [i for i in filter(lambda v: v['class_name'] == 'character', graph_dict["nodes"])][0]["id"]
        objects_in_script = {('character', 1): character_id}
        room_name = None
        for script_line in script:
            for parameter in script_line.parameters:
                # room mapping
                if parameter.name in room_mapping:
                    parameter.name = room_mapping[parameter.name]

                if parameter.name in available_rooms:
                    room_name = parameter.name
                    
                name = parameter.name
                if name in possible_rooms and name not in available_rooms:
                    print("There is no {} in the environment".format(name))
                    return None, False
                if (parameter.name, parameter.instance) not in objects_in_script:
                    objects_in_script[(parameter.name, parameter.instance)] = parameter.instance


        available_nodes = copy.deepcopy(graph_dict['nodes'])
        available_name = list(set([node['class_name'] for node in available_nodes]))

        if room_name == None:
            # Room is not specified in this program, assign one to it
            hist = np.zeros(len(available_rooms_id))
            for obj in objects_in_script:
                obj_name = obj[0]
                if obj_name == 'character':
                    continue
                for node in available_nodes:
                    if node['class_name'] == obj_name:
                        edges = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] in available_rooms_id, graph_dict["edges"])]
                        
                        if len(edges) > 0:
                            for edge in edges:
                                dest_id = edge['to_id']
                                idx = available_rooms_id.index(dest_id)
                                hist[idx] += 1

            if hist.std() < 1e-5:
                # all equal
                room_name = random.choice(available_rooms)
                #print("Set a random_room")
            else:
                idx = np.argmax(hist)
                room_name = available_rooms[idx]
                #print("Pick room: {}".format(room_name))

        room_id = [i["id"] for i in filter(lambda v: v['class_name'] == room_name, graph_dict["nodes"])][0]

        for obj in objects_in_script.keys():
            if obj[0] == 'character':
                pass
            elif obj[0] in available_name:
                added = False
                # existing nodes
                for node in available_nodes:
                    if node['class_name'] == obj[0]:
                        obj_in_room = [i for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] == node['id'] and v['to_id'] == room_id, graph_dict["edges"])]
                        if obj[0] not in available_rooms and len(obj_in_room) == 0:
                            continue
                        else:
                            objects_in_script[obj] = node['id']
                            available_nodes.remove(node)
                            added = True
                            break
                if not added:
                    # add edges
                    graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": self.script_objects_id, "to_id": room_id})
                    node_with_same_class_name = [node for node in filter(lambda v: v["class_name"] == obj[0], graph_dict["nodes"])]
                    category = node_with_same_class_name[0]['category']
                    self._add_missing_node(graph_dict, self.script_objects_id, obj[0], category)
                    objects_in_script[obj] = self.script_objects_id
                    self.script_objects_id += 1
            else:
                # add missing nodes
                graph_dict["edges"].append({"relation_type": "INSIDE", "from_id": self.script_objects_id, "to_id": room_id})
                self._add_missing_node(graph_dict, self.script_objects_id, obj[0], 'placable_objects')
                objects_in_script[obj] = self.script_objects_id
                self.script_objects_id += 1

        # change the id in script
        for script_line in script:
            for parameter in script_line.parameters:

                parameter.instance = objects_in_script[(parameter.name, parameter.instance)]
                
        return objects_in_script, room_mapping

    def prepare_from_precondition(self, precond, objects_in_script, room_mapping, graph_dict):

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
                if k in relation_script_precond_simulator:
                    src_name, src_id = v[0]
                    tgt_name, tgt_id = v[1]
                    src_id = int(src_id)
                    tgt_id = int(tgt_id)
                    # room mapping
                    if tgt_name.lower() in room_mapping:
                        tgt_name = room_mapping[tgt_name.lower()]

                    if k == 'location':
                        assert Room.has_value(tgt_name)

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

    def add_random_objs_graph_dict(self, graph_dict, n):

        object_placing = self.object_placing
        relation_placing_simulator = self.relation_placing_simulator

        objects_to_place = list(object_placing.keys())
        random.shuffle(objects_to_place)
        rooms_id = [node["id"] for node in filter(lambda v: v['class_name'] in self.possible_rooms, graph_dict["nodes"])]

        while n > 0:

            src_name = random.choice(objects_to_place)
            tgt_names = copy.deepcopy(object_placing[src_name])
            random.shuffle(tgt_names)
            for tgt_name in tgt_names:

                tgt_nodes = [i for i in filter(lambda v: v["class_name"] == tgt_name['destination'], graph_dict["nodes"])]

                if len(tgt_nodes) > 0:
                    tgt_node = tgt_nodes[0]
                    tgt_id = tgt_node["id"]

                    self._add_missing_node(graph_dict, self.random_objects_id, src_name, "placable_objects")
                    graph_dict["edges"].append({'relation_type': "INSIDE", "from_id": self.random_objects_id, "to_id": random.choice(rooms_id)})
                    graph_dict["edges"].append({'relation_type': relation_placing_simulator[tgt_name["relation"].lower()], "from_id": self.random_objects_id, "to_id": tgt_id})
                    self.random_objects_id += 1
                    n -= 1
                    break

    def random_change_object_state(self, objects_in_script, graph_dict):

        open_closed = self.open_closed
        on_off = self.on_off
        clean_dirty = self.clean_dirty
        plugged_in_out = self.plugged_in_out
        object_placing = self.object_placing
        object_states = self.object_states
        objects_to_place = list(object_placing.keys())
        states_mapping = self.states_mapping

        object_id_in_program = [i for i in objects_in_script.values()]
        available_states = ['dirty', 'clean', 'open', 'closed', 'free', 'occupied', 'plugged', 'unplugged', 'on', 'off']
        for node in graph_dict["nodes"]:
            if node["id"] in object_id_in_program:
                continue

            if node["class_name"] in object_states:
                possible_states = object_states[node["class_name"]]
                possible_states = [i for i in filter(lambda v: v in available_states, possible_states)]
                if len(possible_states) == 0:
                    continue

                state = random.choice(possible_states)
                if state in ['free', 'occupied']:
                    if state == 'free':
                        self._change_to_totally_free(node, graph_dict)
                    elif state == 'occupied':
                        self._change_to_occupied(node, graph_dict, objects_to_place)
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

    def _change_to_occupied(self, node, graph_dict, objects_to_place):

        if node["class_name"] in SitExecutor._MAX_OCCUPANCIES:
            max_occupancy = SitExecutor._MAX_OCCUPANCIES[node["class_name"]]
            occupied_nodes = [node for node in filter(lambda v: v["relation_type"] == "ON" and v["to_id"] == node["id"] , graph_dict["edges"])]
            current_state = 'free' if len(occupied_nodes) < max_occupancy else "occupied"

            if current_state != "occupied":
                number_objects_to_add = max_occupancy - len(occupied_nodes)
                
                object_placing = self.object_placing
                random.shuffle(objects_to_place)
                                            
                for src_name in objects_to_place:
                    tgt_names = object_placing[src_name]
                    if node["class_name"] in [i["destination"] for i in filter(lambda v: v["relation"] == 'ON', tgt_names)]:
                        self._add_missing_node(graph_dict, self.random_objects_id, src_name, 'placable_objects')
                        graph_dict["edges"].append({"relation_type": "ON", "from_id": self.random_objects_id, "to_id": node["id"]})
                        self.random_objects_id += 1
                        number_objects_to_add -= 0
                        if number_objects_to_add <= 0:
                            break

    def _change_to_totally_free(self, node, graph_dict):

        if node["class_name"] in SitExecutor._MAX_OCCUPANCIES:
            max_occupancy = SitExecutor._MAX_OCCUPANCIES[node["class_name"]]
            occupied_nodes = [node for node in filter(lambda v: v["relation_type"] == "ON" and v["to_id"] == node["id"] , graph_dict["edges"])]
            current_state = 'free' if len(occupied_nodes) < max_occupancy else "occupied"

            if current_state != "free":

                removed_edges = [edge for edge in filter(lambda v: v["relation_type"] == 'ON' and v["to_id"] == node["id"], graph_dict["edges"])]
                remove_object_id = [edge["from_id"] for edge in removed_edges]

                for edge in removed_edges:
                    graph_dict["edges"].remove(edge)
                                        
                floor_id = [node["id"] for node in filter(lambda v: v["class_name"] == 'floor', graph_dict["nodes"])]
                for obj_id in remove_object_id:
                    to_id = random.choice(floor_id)
                    graph_dict["edges"].append({"relation_type": "ON", "from_id": obj_id, "to_id": to_id})
