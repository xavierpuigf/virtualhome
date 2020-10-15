
import pdb
import copy
import random

def convert_action(action_dict):
    agent_do = [item for item, action in action_dict.items() if action is not None]
    # Make sure only one agent interact with the same object
    if len(action_dict.keys()) > 1:
        if None not in list(action_dict.values()) and sum(['walk' in x for x in action_dict.values()]) < 2:
            # continue
            objects_interaction = [x.split('(')[1].split(')')[0] for x in action_dict.values()]
            if len(set(objects_interaction)) == 1:
                agent_do = [random.choice([0,1])]

    script_list = ['']

    for agent_id in agent_do:
        script = action_dict[agent_id]
        if script is None:
            continue
        current_script = ['<char{}> {}'.format(agent_id, script)]

        script_list = [x + '|' + y if len(x) > 0 else y for x, y in zip(script_list, current_script)]

    # script_list = [x.replace('[walk]', '[walktowards]') for x in script_list]
    return script_list


def args_per_action(action):

    action_dict = {'turnleft': 0,
    'walkforward': 0,
    'turnright': 0,
    'walktowards': 1,
    'open': 1,
    'close': 1,
    'putback':1,
    'putin': 1,
    'put': 1,
    'grab': 1,
    'no_action': 0,
    'walk': 1}
    return action_dict[action]


def can_perform_action(action, o1_id, agent_id, graph, 
                       object_restrictions=None, teleport=True):
    """
    Check whether the current action can be done
    Returns None if Action cannot be performed and a fromatted action as a string if yes
    """

    if action == 'no_action':
        return None

    obj2_str = ''
    obj1_str = ''
    id2node = {node['id']: node for node in graph['nodes']}
    o1 = id2node[o1_id]['class_name']
    num_args = 0 if o1 is None else 1
    if num_args != args_per_action(action):
        return None
    
    grabbed_objects = [edge['to_id'] for edge in graph['edges'] if edge['from_id'] == agent_id and edge['relation_type'] in ['HOLDS_RH', 'HOLD_LH']]
    close_edge = len([edge['to_id'] for edge in graph['edges'] if edge['from_id'] == agent_id and edge['to_id'] == o1_id and edge['relation_type'] == 'CLOSE']) > 0
    
    if action == 'grab':
        if len(grabbed_objects) > 0:
            return None

    if action.startswith('walk'):
        if o1_id in grabbed_objects:
            return None
    
    if o1_id == agent_id:
        return None

    if o1_id == agent_id:
        return None

    if (action in ['grab', 'open', 'close']) and not close_edge:
        return None

    if action == 'open':
        if object_restrictions is not None:
            if id2node[o1_id]['class_name'] not in object_restrictions['objects_inside']:
                return None
        if 'OPEN' in id2node[o1_id]['states'] or 'CLOSED' not in id2node[o1_id]['states']:
            return None

    if action == 'close':
        if object_restrictions is not None:
            if id2node[o1_id]['class_name'] not in object_restrictions['objects_inside']:
                return None
        if 'CLOSED' in id2node[o1_id]['states'] or 'OPEN' not in id2node[o1_id]['states']:
            return None

    if 'put' in action:
        if len(grabbed_objects) == 0:
            return None
        else:
            o2_id = grabbed_objects[0]
            if o2_id == o1_id:
                return None
            o2 = id2node[o2_id]['class_name']
            obj2_str = f'<{o2}> ({o2_id})'

    if o1 is not None:
        obj1_str = f'<{o1}> ({o1_id})'
    
    if o1_id in id2node.keys():
        if id2node[o1_id]['class_name'] == 'character':
            return None

    if action.startswith('put'):
        if object_restrictions is not None:
            if id2node[o1_id]['class_name'] in object_restrictions['objects_inside']:
                action = 'putin'
            if id2node[o1_id]['class_name'] in object_restrictions['objects_surface']:
                action = 'putback'
        else:
            if 'CONTAINERS' in id2node[o1_id]['properties']:
                action = 'putin'
            elif 'SURFACES' in id2node[o1_id]['properties']:
                action = 'putback'

    if action.startswith('walk') and teleport:
        action = 'walkto'

    action_str = f'[{action}] {obj2_str} {obj1_str}'.strip()
    # print(action_str)
    return action_str
