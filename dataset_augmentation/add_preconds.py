# Processes all the scripts
# Same as the backup version but without grabbed precond
import glob
import numpy as np
import os
import json
import ipdb
from augmentation_utils import *

dump_preconds = False
rooms = [x.lower() for x in [
        'Kitchen',
        'Bathroom',
        'Living_Room',
        'Dining_Room',
        'Bedroom',
        'Kids_Bedroom',
        'Entrance_Hall',
        'Home_office']]

body_parts = [x.lower() for x in 
              ['HANDS_BOTH', 'ARMS_LEFT', 'HANDS_LEFT', 'FACE', 
              'ARMS_RIGHT', 'HANDS_RIGHT', 'HAIR', 'ARMS_BOTH', 
              'LEGS_BOTH', 'FEET_BOTH', 'EYES_BOTH', 'TEETH']]
objects_occupied = [
    'couch',
    'bed',
    'chair',
    'loveseat',
    'sofa',
    'toilet',
    'pianobench',
    'bench']

tables_and_surfaces = ['DESK', 'TABLE', 'COFFEE_TABLE', 'BED', 'SINK', 'CABINET', 'BOOKSHELF', 
                       'CLOSET', 'BASKET_FOR_CLOTHES', 'FILING_CABINET', 'KITCHEN_COUNTER', 'KITCHEN_CABINET', 
                        'BATHROOM_CABINET', 'BATHROOM_COUNTER', 'CUPBOARD', 'TOOTHBRUSH_HOLDER', 'DRESSER']

class ScriptFail(BaseException):
    def __init__(self, m):
        self.message = m
    def __str__(self):
        return self.message

def get_preconds_script(script_lines):
    content = script_lines
    # Plugget_out precond
    is_plugged = {}
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if len(obj_names) == 0:
            continue
        obj_id = (obj_names[0], ins_num[0])
        if action.upper() == 'PLUGOUT':
            if obj_id in is_plugged.keys() and not is_plugged[obj_id]:
                print('Error, already plugged out')
            else:
                is_plugged[obj_id] = False
        if action.upper() == 'PLUGIN':
            if obj_id not in is_plugged.keys():
                # Never plugged out, so precond is plugin
                precond_dict.addPrecond('unplugged', obj_id, [])
            elif is_plugged[obj_id]:
                raise ScriptFail('Error, object plugged in twice')
            is_plugged[obj_id] = True

    # Check for things that are on at the start
    is_on = {}
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if len(obj_names) == 0:
            continue
        obj_id = (obj_names[0], ins_num[0])
        if action == 'SwitchOff':
            if obj_id not in is_on.keys(): # If this light was never switched on/off
                precond_dict.addPrecond('is_on', obj_id, [])
                # If it was not plugged, needs to be plugged
                if hasProperty(obj_id[0], 'HAS_PLUG'):
                    if obj_id not in precond_dict.obtainCond('unplugged'):
                        precond_dict.addPrecond('plugged', obj_id, [])

            else:
                if not is_on[obj_id]:
                    raise ScriptFail('Error, object turned off twice')
            is_on[obj_id] = False

        if action == 'SwitchOn':
            if obj_id in is_on.keys() and is_on[obj_id]:
                print('\n'.join(content))
                raise ('Error, object turned on twice')
            elif obj_id not in is_on.keys():
                precond_dict.addPrecond('is_off', obj_id, [])
                # If it was not plugged, needs to be plugged
                if hasProperty(obj_id[0], 'HAS_PLUG'):
                    if obj_id not in precond_dict.obtainCond('unplugged'):
                        precond_dict.addPrecond('plugged', obj_id, [])

            is_on[obj_id] = True


    # Check objects of interaction while sitting
    is_sitting = None
    obj_location = {}
    object_grabbed = {}
    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if action in ['Sit', 'Lie']:
            is_sitting = (obj_names[0], ins_num[0])
        elif action in ['StandUp', 'Walk', 'Run']:
            is_sitting = None

        else:
            if len(obj_names) > 0:
                obj_id = (obj_names[0], ins_num[0])

            if action in ['PutBack', 'PutObjBack', 'PutIn']:
                if obj_id in object_grabbed.keys():
                    del object_grabbed[obj_id]
                if action in ['PutBack', 'PutIn']:
                    obj_location[obj_id] = (obj_names[1], ins_num[1])
                else:
                    if obj_id in obj_location.keys():
                        del obj_location[obj_id]
            if is_sitting is not None and obj_id not in object_grabbed.keys() and obj_id != is_sitting:
                # If you did put the object somewhere, this somewhere should be close to the sitting place
                if obj_id in obj_location.keys() and obj_location[obj_id] != is_sitting:
                    precond_dict.addPrecond('atreach', is_sitting, [obj_location[obj_id]]) 
                else:
                    precond_dict.addPrecond('atreach', is_sitting, [obj_id])

            if action == 'Grab':
                object_grabbed[obj_id] = True
    # If the character's first action is standup (no sitting before), then precond is it
    is_sitting = False
    is_lying = False
    ever_sitting = False
    ever_lying = False
    # If the character's first action is standup (no sitting before), then precond is it
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if action == 'Sit':
            if (not is_sitting) and (not is_lying):
                is_sitting = True
            else:
                raise ScriptFail('Error, character already sitting')
                # print('\n'.join(content))
        if action == 'Lie':
            is_lying = True
        if action.upper() in ['STANDUP', 'WAKEUP']:
            if is_sitting or is_lying:
                is_sitting = False
                is_lying = False
            else:
                if ever_sitting or ever_lying:
                    raise ScriptFail('Error, character already up')
                else:
                    precond_dict.addPrecond('sitting', ('Character', 1), [])


    # Make sure you walk to find an object before interacting
    # Infer state
    found_object = {}
    insert_in = []
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        # If object has not been found add a find
        if len(obj_names) > 0:
            if action.upper() in ['WALK', 'RUN', 'FIND']:
                found_object[(obj_names[0], ins_num[0])] = True
            elif action.upper() not in ['PUTOFF']:
                if (obj_names[0], ins_num[0]) not in found_object.keys():
                    insert_in.append([i, '[Find] <{0}> ({1})'.format(
                        obj_names[0], ins_num[0])])
                    found_object[(obj_names[0], ins_num[0])] = True

                # Second object as well
                if len(obj_names) > 1:
                    if (obj_names[1], ins_num[1]) not in found_object.keys():
                        insert_in.append([i, '[Find] <{0}> ({1})'.format(
                            obj_names[1], ins_num[1])])
                        found_object[(obj_names[1], ins_num[1])] = True
            else:
                # the object has been putoff so no need to find
                found_object[(obj_names[0], ins_num[0])] = True
    
    if len(insert_in) > 0: 
        for x in insert_in:
            if x not in precond_dict.obtainCond('inside'):
                precond_dict.addPrecond('nearby', (parseStrBlock(x[1])[1][0], parseStrBlock(x[1])[2][0]), [])
    

    # The first time you interact with a non grabbed object in a room
    # you should walk to it
    object_grabbed = {}
    last_walked = None
    insert_in = []

    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if len(obj_names) > 0:
            object_id = (obj_names[0], ins_num[0])
        else:
            continue

        if action.upper() in ['RUN', 'WALK']:
            last_walked = object_id
        else:
            if object_id not in object_grabbed.keys() or not object_grabbed[object_id]:
                # if we last walked to a room, we should walk towards the object
                if last_walked is not None and last_walked[0].lower() in rooms:
                    raise ScriptFail('Error, we should be walking towards the object first')
                else:
                    if last_walked is not None and last_walked != object_id:
                        # if we last walked towards an object, this new object should be close
                        precond_dict.addPrecond('atreach', object_id, [last_walked])

                    l = 0

            if action.upper() in ['GRAB', 'PUTON']:
                object_grabbed[object_id] = True

            if action.upper() in ['PUTOBJBACK', 'PUTBACK', 'PUTOFF']:
                object_grabbed[object_id] = False


    # If you put off some clothes that you did not puton, you were wearing them
    # And before putoff you need to add a find
    insert_in = []
    puton = {}
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if len(obj_names) > 0:
            object_id = (obj_names[0], ins_num[0])
        if action.upper() == 'PUTOFF':
            if object_id not in puton.keys():
                insert_in.append([i, '[Find] <{0}> ({1})'.format(
                    obj_names[0], ins_num[0])])
                precond_dict.addPrecond('in', object_id, [('Character', 1)])
                puton[object_id] = False
            else:
                if not puton[object_id]:
                     raise ScriptFail('Error, this was already off')

    # Generate more spatial preconds
    is_open = {}
    last_room = None
    last_open = []
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if len(obj_names) == 0: continue
        object_id = (obj_names[0], ins_num[0])

        # Check on which room an object could be
        if obj_names[0] in rooms: last_room = (obj_names[0], ins_num[0])
        elif last_room is not None and action is not 'PutOff':
            precond_dict.addPrecond('location', object_id, [last_room])
        if action.upper() == 'OPEN':
            if object_id not in is_open.keys():
                precond_dict.addPrecond('closed', object_id, [])
            last_open.append(object_id)
            is_open[object_id] = True
        if action.upper() == 'CLOSE': 
            try:
                is_open[object_id] = False
                last_open = [x for x in last_open if x != object_id]
            except:
                if object_id[0].upper() != 'EYES_BOTH':
                    precond_dict.addPrecond('open', object_id, [])

        # If something is not closed, it generally means we are grabbing the stuff from it
        if action.upper() == 'GRAB' and len([x for x in is_open.keys() if is_open[x]]) > 0:
            prev_conds_inside = precond_dict.obtainCond('inside')
            prev_conds_in = precond_dict.obtainCond('in')
            objects_wearing = [x for x in prev_conds_in]
            objects_inside = [x for x in prev_conds_inside]
            obj12 = objects_wearing + objects_inside
            if object_id not in obj12:
                precond_dict.addPrecond('inside', object_id, [last_open[-1]])
            
    
    # Check already existing relations
    existing_relations = []
    for rel in ['inside']:
        existing_relations += precond_dict.obtainCond(rel)
    object_grabbed = {}

    # Check for finds that dont have interaction afterwards,
    # this means that the second object should be nearby the first
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if action in ['Walk', 'Run', 'Find', 'LookAt']:
            if i+1 < len(content):
                action2, obj_names2, ins_num2 = parseStrBlock(content[i+1])
                if len(obj_names2) > 0:
                    obj_id = (obj_names[0], ins_num[0])
                    
                    newobj = [(obj_names2[it], ins_num2[it]) for it in range(len(obj_names2)) if obj_names2[it].upper() not in rooms]
                    if len(newobj) > 0:
                        if newobj[0] in object_grabbed.keys() or obj_id in object_grabbed.keys(): 
                            continue
                        
                        if obj_id not in newobj and str(newobj[0]) not in existing_relations and obj_id[0] not in rooms:
                            print('HERE')
                            if obj_id[0].upper() in tables_and_surfaces and len(newobj) < 2:
                                preposition = 'in'
                                if newobj[0][0].upper() == 'CHAIR':
                                    preposition = 'nearby'
                                
                                precond_dict.addPrecond(preposition, newobj[0], [obj_id])
                            else:
                                if obj_id[0].upper() in ['COMPUTER', 'LAPTOP']: continue
                                if newobj[0][0].upper() in ['ARMS_BOTH', 'HAIR', 'FACE']: continue
                                #print('SPATIAL RELATION', i, newobj, obj_id, script_name)
        if action == 'Grab':
            obj_id = (obj_names[0], ins_num[0])
            object_grabbed[obj_id] = True

    
    # If sit and watch, the object you sit should be facing
    is_sitting = None
    obj_location = {}
    for i in range(len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        if action in ['Sit', 'Lie']:
            is_sitting = (obj_names[0], ins_num[0])
        elif action in ['StandUp', 'Walk', 'Run']:
            is_sitting = None

        else:
            if len(obj_names) > 0:
                obj_id = (obj_names[0], ins_num[0])

            if action in ['Watch']:
                if is_sitting is not None:
                    precond_dict.addPrecond('facing', is_sitting, [obj_id])

    # Add free precond

    for i in range(len(content)):
        is_couch = False
        curr_block = content[i]
        action, obj_names, ins_num = parseStrBlock(curr_block)
        for (obj_name, idi) in zip(obj_names, ins_num):
            if obj_name in objects_occupied:
                precond_dict.addPrecond('free', (obj_name, idi), [])

    # inside = {}
    # to_keep = []
    # if 'inside' in precond_dict.keys():
    #     for elem in precond_dict['inside']:
    #         obj = elem.split(' --> ')[0]
    #         if obj not in inside.keys():
    #             inside[obj] = True
    #         else:
    #             continue
    #         to_keep.append(elem)
    # if 'inside' in precond_dict.keys(): precond_dict['inside'] = to_keep
    # for cond in ['location', 'nearby']:
    #    for elem in list(precond_dict.obtainCond(cond)):
    #        if elem in precond_dict.obtainCond('inside'):
    #             precond_dict.removeCond(cond, elem)


    

    return precond_dict

def compare_preconds(precond_dict1, precond_dict2):
    def to_hash(precond_list):
        pr_list = precond_list.copy()
        for it, elem in enumerate(pr_list):
            # dictionary of lists
            key_elem = list(elem)[0]
            values = elem[key_elem]
            for v_id, v in enumerate(values):
                if isinstance(v, list):
                    values[v_id] = tuple(v)
           
            values = tuple(values)
            tuple_dict = (key_elem, values)
            pr_list[it] = tuple_dict
        
        # All at reach should be intercheanchable
        to_add = []
        pr_list = [x for x in pr_list if not (x[0] == 'atreach' and x[1][0] == x[1][1])]
        # for item in pr_list:
        #     if item[0] == 'atreach':
        #         reversed_at_reach = (item[0], (item[1][1], item[1][0]))
        #         if reversed_at_reach not in pr_list:
        #             to_add.append(reversed_at_reach)
        # pr_list += to_add
        return sorted(pr_list)

    l1 = to_hash(precond_dict1)
    l2 = to_hash(precond_dict2)
    inter = len(set(l1).intersection(set(l2)))
    union = len(set(l1).union(set(l2)))
    
    if inter != union:
        # print('Intersection {} Union {}'.format(inter, union))
        # print('Intersection')
        # print(list(set(l1).intersection(l2)))
        
        if len(list(set(l1) - set(l2))) > 0:
            print('Missing')
            print(list(set(l1) - set(l2)))
            print(set(l1))
            print('Extra')
            print(list(set(l2) - set(l1)))
            print('\n')
            return False
            
        return True

    return True

path_scripts = '../../../../data/data_andrew_changed_march_13/programs_processed_precond_nograb_morepreconds/withoutconds/*/*.txt'
#path_scripts = '../../../../data/data_march_12/programs_processed_precond_nograb_morepreconds/withoutconds/*/*.txt'

all_scripts = sorted(glob.glob(path_scripts))
all_scripts = [x for x in all_scripts if '/'.join(x.split('/')[-2:]) == 'results_text_rebuttal_specialparsed_programs_turk_third/split99_4.txt']
print(len(all_scripts))
cont_bad = 0
for script_name in all_scripts:
    precond_dict = Precond()
    script_name_in = script_name
    script_name_out = script_name.replace('withoutconds', 'initstate').replace('.txt', '.json')


    with open(script_name_in, 'r') as f:
        content = f.readlines()[4:]
    content = [x.strip() for x in content]
    try:
        precond_dict = get_preconds_script(content)
    except ScriptFail as e:
        #print(e, script_name)
        continue
    with open(script_name_out, 'r') as f:
        previous_preconds = json.load(f)

    #previous_preconds
    new_preconds = precond_dict.printCondsJSON()
    res = compare_preconds(previous_preconds, new_preconds)
    print(new_preconds)
    if not res:
        cont_bad += 1
        print('\n'.join(content))
        print('\n')
        pass;
        #ipdb.set_trace()
    if dump_preconds:
        json_file = script_name_out
        if not os.path.isdir(os.path.dirname(json_file)):
            os.makedirs(os.path.dirname(json_file))
        with open(json_file, 'w+') as f:
            f.write(json.dumps(precond_dict.printCondsJSON()))

print(cont_bad, len(all_scripts))
