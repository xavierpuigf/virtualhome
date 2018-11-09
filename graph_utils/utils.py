import re
import ipdb

state_node = ['is_on', 'is_off', 'plugged', 'unplugged', 'open', 'closed', 'clean', 'dirty', 'sitting', 'lying']
state_edge = ['inside', 'location', 'atreach', 'in']
equivalent_rooms = {
        "kitchen": ["dining_room"], 
        "dining_room": ["kitchen"], 
        "entrance_hall": ["living_room"], 
        "home_office": ["living_room"], 
        "living_room": ["home_office", "entrance_hall"],
        "kids_bedroom": ["bedroom"],
        "bedroom": ["kids_bedroom", "bedroom"]
    }

map_state = {
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
map_edge = {
        "inside": "INSIDE", 
        "location": "INSIDE", 
        "atreach": "CLOSE", 
        "in": "ON"
}

def parse_mapping(instructions):
    # Given all the instructions obtain map from script id to graph id
    instructions = instructions[4:]
    dict_mapping = {}
    for instruction in instructions:
        arguments = re.findall('\<[^\<]*\> \([0-9]+\.[0-9]+\)', instruction.strip()) 
        for argument in arguments:
            argname = argument.split('>')[0][1:]
            argid = argument.split('(')[1][:-1]

            argnames = [argname]
            if argname in list(equivalent_rooms.keys()):
                argnames += equivalent_rooms[argname]
            for arg in argnames:    
                tuplen = (arg, argid.split('.')[0])
                idn = argid.split('.')[1]
                if tuplen in dict_mapping.keys() and dict_mapping[tuplen] != idn:
                    raise Exception
                dict_mapping[tuplen] = idn
    return dict_mapping

def precond_to_id(json_precond, mapping):
    # Given the json with preconds, convert to a subgraph
    sub_graph = {'nodes': [], 'edges': []}
    for precon in json_precond:
        relation_name = list(precon.keys())[0]
        if relation_name in state_node:
            if precon[relation_name][0] == 'character':
                continue
            node_id = mapping[tuple(precon[relation_name])]
            translated_precond = map_state[relation_name]
            sub_graph['nodes'].append((node_id, translated_precond))
        elif relation_name in state_edge:
            if precon[relation_name][0][0] == 'character':
                continue
            if precon[relation_name][1][0] == 'character':
                continue
            node_id1 = mapping[tuple(precon[relation_name][0])]
            node_id2 = mapping[tuple(precon[relation_name][1])]
            trans_rel = map_edge[relation_name]
            sub_graph['edges'].append((node_id1, trans_rel, node_id2))
        else:
            pass
    return sub_graph
