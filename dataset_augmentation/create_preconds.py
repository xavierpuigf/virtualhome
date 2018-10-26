# Processes all the scripts
# Same as the backup version but without grabbed precond
import glob
import numpy as np
import script_utils
import os
from utils_preconds import *
import json
import pdb, ipdb
num_lines = []
errors_putback = 0
already_grb = 0
all_scripts = glob.glob('programs_processed_precond_nograb/withoutconds/*/*.txt')
not_found = []
object_conversion_map = {}
rooms = [x.upper() for x in ['Kitchen',
        'Bathroom',
        'Living Room',
        'Dining Room',
        'Bedroom',
        'Kids Bedroom',
        'Entrance Hall',
        'Home office']]

dict_all_scripts = {}

actions_no_object = ['StandUp', 'Jump', 'Call', 'WakeUp', 'Sleep', 'Wait', 'Laugh', 'Speak', 'Sing', 'Play']
actions_2_object =  ['PutBack', 'Pour', 'Throw', 'Cover', 'Wrap', 'Soak', 'Spread']

body_parts = ['HANDS_BOTH', 'ARMS_LEFT', 'HANDS_LEFT', 'FACE', 'ARMS_RIGHT', 
              'HANDS_RIGHT', 'HAIR', 'ARMS_BOTH', 'LEGS_BOTH', 'FEET_BOTH', 'EYES_BOTH', 'TEETH']
conte = 0

objects_occupied = [
    'couch',
    'bed',
    'chair',
    'loveseat',
    'sofa',
    'toilet',
    'pianobench',
    'bench']

print(len(all_scripts))
for script_name in all_scripts:
    precond_dict = Precond()
    script_name_in = script_name
    script_name_out = script_name.replace('programs_processed_precond_nograb/withoutconds/', 'programs_processed_precond_nograb_morepreconds/withconds/')
    script_name_out2 = script_name.replace('programs_processed_precond_nograb/withoutconds/', 'programs_processed_precond_nograb_morepreconds/withoutconds/')
    with open(script_name, 'r') as f:
        content = [x.strip() for x in f.readlines()]

    if tuple(content) in dict_all_scripts.keys():
        print('File {} repeated'.format(script_name))
        continue
    dict_all_scripts[tuple(content)] = True

    if content is None:
        # Remove file
        print('Remove')
        continue
    
    # Standarize format, props do not appear
    content[2] = ''
    content[3] = ''


    # Check which objects are found, as this cannot be added as precond
    obj_found = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        # If object has not been found add a find
        if len(obj_names) > 0:
            if action.upper() in ['WALK', 'RUN', 'FIND']:
                obj_found[(obj_names[0], ins_num[0])] = True

    # cellphone and type
    is_grabbed = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action == 'Type' and obj_names[0] in ['CELLPHONE', 'TELEPHONE']:
            if (obj_names[0], ins_num[0]) in is_grabbed.keys():
                content[i].replace('Touch', 'Type')
            else: print('should_delete')
        if action in ['Grab', 'Lift']:
            is_grabbed[(obj_names[0], ins_num[0])] = True
        if action in ['PutBack', 'PutObjBack', 'Drop']:
            if (obj_names[0], ins_num[0]) in is_grabbed.keys():
                del is_grabbed[obj_names[0], ins_num[0]]


    all_objects_aux = [script_utils.parseStrBlock(content[i])[1] for i in range(4, len(content))]
    all_objects = [x[0] for x in all_objects_aux if len(x) > 0]
    all_objects += [x[1] for x in all_objects_aux if len(x) > 1] 
    if 'BUTTON' in all_objects:
        if ('REMOTE CONTROL' not in all_objects and 'COMPUTER' not in all_objects and 'LIGHT' not in all_objects and 
            'TELEVISION' not in all_objects and 'COFFE MAKER' not in all_objects  and
            'CD PLAYER' not in all_objects and 'PHONE' not in all_objects and 'CELLPHONE' not in all_objects and 'TELEPHONE' not in all_objects and
            'TOASTER' not in all_objects and 'RADIO' not in all_objects and 'DISHWASHER' not in all_objects and 'WASHING MACHINE' not in all_objects):
            #print script_name, set(all_objects)
            # print script_name, 'is regular button'
            l = 0 
        else:
            if not ('LIGHT' not in all_objects and
            'CD PLAYER' not in all_objects and 'PHONE' not in all_objects and 'CELLPHONE' not in all_objects and 'TELEPHONE' not in all_objects and
            'TOASTER' not in all_objects and 'RADIO' not in all_objects and 'DISHWASHER' not in all_objects and 'WASHING MACHINE' not in all_objects):
                #print script_name, set(all_objects)
                l = 0
            else:
                l= 0
                #print 'Correct', script_name

    # Plugget_out precond
    is_plugged = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
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
                print('Error, object plugged in twice')
                print('\n'.join(content))
            is_plugged[obj_id] = True

    # Check for things that are on at the start
    # Here we will check also for plugged preconds
    is_on = {}
    nl = 0
    to_delete = []
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
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
                    raise 'Error, object turned off twice'
                    pdb.set_trace()
            is_on[obj_id] = False

        if action == 'SwitchOn':
            if obj_id in is_on.keys() and is_on[obj_id]:
                # print script_name
                to_delete.append(i)
                print('\n'.join(content))
                print('Error, object turned on twice')
                # pdb.set_trace()
            elif obj_id not in is_on.keys():
                precond_dict.addPrecond('is_off', obj_id, [])

                # If it was not plugged, needs to be plugged
                if hasProperty(obj_id[0], 'HAS_PLUG'):
                    if obj_id not in precond_dict.obtainCond('unplugged'):
                        precond_dict.addPrecond('plugged', obj_id, [])

            is_on[obj_id] = True        

    content = removeInstructions(to_delete, content)

    # If you put an object in a cabinet/dishwasher make sure you open it first
    # Infer state
    object_open = {}
    open_recipients = ['FRIDGE', 'DISHWASHER', 'CABINET', 'KITCHEN CABINET', 
                       'BATHROOM CABINET', 'CABINET', 'DESK', 'FOLDER', 'CUPBOARD', 
                       'COFFE MAKER', 'OVEN', 'CLOSET', 'DRESSER', 'MICROWAVE', 
                       'FILING CABINET', 'WASHING MACHINE', 'CLOSET', 'CLOSET']

    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: object_id = (obj_names[0], ins_num[0])
        if action.upper() == 'OPEN' and obj_names[0] in open_recipients:
            object_open[object_id] = True
        
        if action.upper() == 'CLOSE' and obj_names[0] in open_recipients:
            try: 
                del object_open[object_id]
            except: 
                pdb.set_trace()
                print('Object closed before opening', script_name, object_id)
        if action.upper() in ['PUTBACK', 'POUR']:
            try:
                if obj_names[1] in open_recipients:
                    second_object_id = (obj_names[1], ins_num[1])
                    if second_object_id not in object_open.keys():
                        object_open[second_object_id] = True
                        #print script_name, content[1]
                        #pdb.set_trace()
            except:
                print(content[i], script_name)
    

    # If a dishwasher, washing machine is switched on, make sure it is closed first
    is_open = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0:
            if obj_names[0] in ['WASHING MACHINE', 'DISHWASHER']:
                if action == 'Open':
                    is_open[(obj_names[0], ins_num[0])] = True
                if action == 'Close':
                    is_open[(obj_names[0], ins_num[0])] = False



    # If you read an object make sure you grab it first, unless it was already grabbed
    # Infer state
    object_grabbed = {}
    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True

    val = 0
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        else: 
            continue
        if action.upper() == 'GRAB':
            object_grabbed[object_id] = True

        if action.upper() in ['PUTBACK', 'PUTOBJBACK', 'DROP'] and object_id in object_grabbed.keys() and object_grabbed[object_id]:
            object_grabbed[object_id] = False


    # If you putback an object, make sure you grab it first
    # Infer state
    object_grabbed = {}
    last_found = {}
    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    val = 0
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        else: 
            continue
        if action.upper() == 'FIND':
            last_found[object_id] = i
        if action.upper() == 'GRAB':
            object_grabbed[object_id] = True
        
        if action.upper() in ['PUTOBJBACK', 'PUTBACK', 'DROP'] and obj_names[0] not in body_parts:
            if object_id in object_grabbed.keys() and object_grabbed[object_id]:
                object_grabbed[object_id] = False
            
            if object_id in last_found.keys(): del last_found[object_id]


    # If you pour something and not grabbed make sure you grab it

    # Check objects of interaction while sitting

    is_sitting = None
    obj_location = {}
    object_grabbed = {}
    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action in  ['Sit', 'Lie']:
            is_sitting = (obj_names[0], ins_num[0])
        elif action in ['StandUp', 'Walk', 'Run']:
            is_sitting = None

        else:

            if len(obj_names) > 0:
                obj_id = (obj_names[0], ins_num[0])


            if action in ['PutBack', 'PutObjBack']:
                if obj_id in object_grabbed.keys():
                    del object_grabbed[obj_id]
                if action == 'PutBack':
                    obj_location[obj_id] = (obj_names[1], ins_num[1])
                else:
                    if obj_id in obj_location.keys(): del obj_location[obj_id]
            if is_sitting is not None and obj_id not in object_grabbed.keys():
                # If you did put the object somewhere, this somewhere should be close to the sit
                if obj_id in obj_location.keys():
                    precond_dict.addPrecond('atreach', is_sitting, [obj_location[obj_id]]) 
                else:
                    precond_dict.addPrecond('atreach', is_sitting, [obj_id])

            if action == 'Grab':
                object_grabbed[obj_id] = True
    

    is_sitting = False
    is_lying = False
    ever_sitting = False
    ever_lying = False
    # If the character's first action is standup (no sitting before), then precond is it
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action == 'Sit':
            if (not is_sitting) and (not is_lying):
                is_sitting = True
            else:
                print('Error, character already sitting')
                # print('\n'.join(content))
        if action == 'Lie':
            is_lying = True
        if action.upper() in ['STANDUP', 'WAKEUP']:
            if is_sitting or is_lying:
                is_sitting = False
                is_lying = False
            else:
                if ever_sitting or ever_lying:
                    print('Error, character already up')
                else:
                    precond_dict.addPrecond('sitting', ('Character', 1), [])

    # Make sure you find an object before interacting
    # Infer state
    found_object = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        # If object has not been found add a find
        if len(obj_names) > 0:
            if action.upper() in ['WALK', 'RUN', 'FIND']:
                found_object[(obj_names[0], ins_num[0])] = True
            elif action.upper() not in ['PUTOFF']:
                if (obj_names[0], ins_num[0]) not in found_object.keys():
                    found_object[(obj_names[0], ins_num[0])] = True

                # Second object as well
                if len(obj_names) > 1:
                    if (obj_names[1], ins_num[1]) not in found_object.keys():
                        found_object[(obj_names[1], ins_num[1])] = True
            else:
                # the object has been putoff so no need to find
                found_object[(obj_names[0], ins_num[0])] = True

    # When you Pour an object, if you had not grabbed you should walk to it
    insert_in = []
    object_grabbed = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        else: 
            continue

        if action.upper() in ['POUR']:
            if object_id not in object_grabbed.keys() or not object_grabbed[object_id]:
                prev_action, prev_obj_names, prev_ins_num = script_utils.parseStrBlock(content[i-1])
                if prev_action.upper() == 'FIND' and object_id == (prev_obj_names[0], prev_ins_num[0]):
                    insert_in.append([i-1, '[Walk] <{0}> ({1})'.format(
                                     obj_names[0], ins_num[0])])
                    insert_in.append([i, '[Grab] <{0}> ({1})'.format(
                                     obj_names[0], ins_num[0])])
                    object_grabbed[object_id] = True
                else:
                    print('Difficult case POUR')
                    #print('/n'.join(content))
                    #pdb.set_trace()

        if action.upper() in ['GRAB', 'PUTON']:
            object_grabbed[object_id] = True
        
        if action.upper() in ['PUTOBJBACK', 'PUTBACK', 'PUTOFF']:
            object_grabbed[object_id] = False
    content = insertInstructions(insert_in, content)



    # The first time you interact with a non grabbed object in a room
    # you should walk to it
    object_grabbed = {}
    last_walked = None
    insert_in = []

    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        else: 
            continue

        if action.upper() in ['RUN', 'WALK']:
            last_walked = object_id
        else:
            if object_id not in object_grabbed.keys() or not object_grabbed[object_id]:
                # if we last walked to a room, we should walk towards the object
                if last_walked is not None and last_walked[0].upper() in rooms:
                    last_walked = object_id
                    insert_in.append([i, '[Walk] <{0}> ({1})'.format(
                        obj_names[0], ins_num[0])])
                else:
                    if last_walked is not None:
                        # if we last walked towards an object, this new object should be close
                        precond_dict.addPrecond('atreach', object_id, [last_walked]) 

                    l = 0

            if action.upper() in ['GRAB', 'PUTON']:
                object_grabbed[object_id] = True
            
            if action.upper() in ['PUTOBJBACK', 'PUTBACK', 'PUTOFF']:
                object_grabbed[object_id] = False

    content = insertInstructions(insert_in, content)

    # Make sure you do not turn to an object if you are grabbing it
    object_grabbed = {}
    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    val = 0
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        else: 
            continue

        if action.upper() == 'GRAB':
            object_grabbed[object_id] = True
        
        if action.upper() in ['PUTOBJBACK', 'PUTBACK', 'PUTOFF']:
            try:
                object_grabbed[object_id] = False
            except:
                print('Error', script_name, object_id)
                continue

    
    # Subsitute cabinet
    last_room = 'CABINET'
    bookshelf_appears = False
    for i in range(4, len(content)):
        content_element = content[i]
        if 'BOOKSHELF' in content_element:
            bookshelf_appears = True
    for i in range(4, len(content)):
        elem = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(elem)
        if len(obj_names) > 0 and obj_names[0] in rooms:
            last_room = obj_names[0]

        if 'CABINET' in obj_names:
            if last_room == 'KITCHEN': new_object = 'KITCHEN CABINET'
            elif last_room == 'BATHROOM': new_object = 'BATHROOM CABINET'    
            else:   
                if ('bookshelf' in content[0] or 'bookshelf' in content[1] or 
                    'book shelf' in content[0] or 'book shelf' in content[1] and not bookshelf_appears):
                    new_object = 'BOOKSHELF'
                else: new_object = 'CABINET'
            content[i] = content[i].replace('CABINET', new_object)


    # If you put off some clothes that you did not puton, you were wearing them
    # And before putoff you need to add a find
    insert_in = []
    puton = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
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
                     print('Error, this was already off')
    content = insertInstructions(insert_in, content)

    # Generate more spatial preconds
    is_open = {}
    last_room = None
    last_open = []
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
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
                if object_id[0] != 'EYES_BOTH':
                    precond_dict.addPrecond('open', object_id, [])

        # If something is not closed, it generally means we are grabbing the stuff from it
        # As long as this was never found before opening this thing
        if action.upper() == 'GRAB' and len([x for x in is_open.keys() if is_open[x]]) > 0:

            prev_conds_inside = precond_dict.obtainCond('inside')
            prev_conds_in = precond_dict.obtainCond('in')
            objects_wearing = [x for x in prev_conds_in]
            objects_inside = [x for x in prev_conds_inside]
            obj12 = objects_wearing + objects_inside
            if object_id not in obj12:
                precond_dict.addPrecond('inside', object_id, [last_open[-1]])
            
    
    # Check already existing relations
    already_relations = []
    for rel in ['inside']:
        already_relations += precond_dict.obtainCond(rel)
        

    # Check for finds that dont have interaction afterwards, 
    # this means that the second object should be nearby hr first
    object_grabbed = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action in ['Walk', 'Run', 'Find', 'LookAt']:
            if i+1 < len(content):
                action2, obj_names2, ins_num2 = script_utils.parseStrBlock(content[i+1])
                if len(obj_names2) > 0:
                    obj_id = (obj_names[0], ins_num[0])
                    
                    newobj = [(obj_names2[it], ins_num2[it]) for it in range(len(obj_names2)) if obj_names2[it].upper() not in rooms]
                    if len(newobj) > 0:
                        if newobj[0] in object_grabbed.keys() or obj_id in object_grabbed.keys(): 
                            continue
                        
                        if obj_id not in newobj and str(newobj[0]) not in already_relations and obj_id[0] not in rooms:
                            if obj_id[0] in ['DESK', 'TABLE', 'COFFEE TABLE', 'BED', 'SINK', 'CABINET', 'BOOKSHELF', 'CLOSET', 'BASKET FOR CLOTHES', 'FILING CABINET', 'KITCHEN COUNTER', 'KITCHEN CABINET', 
                                             'BATHROOM CABINET', 'BATHROOM COUNTER', 'CUPBOARD', 'TOOTHBRUSH HOLDER', 'DRESSER'] and len(newobj) < 2:
                                preposition = 'in'
                                if newobj[0][0] == 'CHAIR':
                                    preposition = 'nearby'
                                
                                precond_dict.addPrecond(preposition, newobj[0], [obj_id])
                            else:
                                if obj_id[0] in ['COMPUTER', 'LAPTOP']: continue
                                if newobj[0][0] in ['ARMS_BOTH', 'HAIR', 'FACE']: continue
                                # print 'SPATIAL RELATION', i, newobj, obj_id, script_name
        if action == 'Grab':
            obj_id = (obj_names[0], ins_num[0])
            object_grabbed[obj_id] = True

    # If we look at something make sure we turn to it
    currently_facing = None
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0:
            obj_id = (obj_names[0], ins_num[0])
        if action.upper() in ['FIND', 'WALK']:
            currently_facing = None
        if action.upper() == 'TURNTO':
            currently_facing = obj_id
        if action.upper() in ['LOOKAT', 'POINTAT']:
            if currently_facing != obj_id:
                insert_in.append([i, '[TurnTo] <{0}> ({1})'.format(
                    obj_names[0], ins_num[0])])
    content = insertInstructions(insert_in, content)

    # If sit and watch, the object you sit should be facing
    is_sitting = None
    obj_location = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
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

    # Eliminate duplicate preconds
    # 1. Only keep the first time something is inside
    # 2. If something is inside, we dont need to set something in location
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
    #for cond in ['location', 'nearby']:
    #    for elem in list(precond_dict.obtainCond(cond)):
    #        if elem in precond_dict.obtainCond('inside'):
    #            precond_dict.removeCond(cond, elem)
    #
    # Good proxy for scripts that are bad (bad AMT workers)
    for i in range(4, len(content)-2):

        action1, obj_names1, ins_num = script_utils.parseStrBlock(content[i])
        action2, obj_names2, ins_num = script_utils.parseStrBlock(content[i+1])
        action3, obj_names3, ins_num = script_utils.parseStrBlock(content[i+2])
        if action1.upper() == 'FIND' and action2.upper() == 'POINTAT' and action3.upper() == 'LOOKAT':            
            if obj_names1[0] == obj_names2[0] and obj_names1[0] == obj_names3[0]:
                print(script_name, 'lookat, pointat')

    
    # turn objects to lowercase and add free precond
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        obj_old_to_new = {obj_name: obj_name.lower().replace(' ', '_') for obj_name in obj_names}
        for (obj_name, idi) in zip(obj_names, ins_num):
            if obj_name.lower().replace(' ', '_') in objects_occupied:
                precond_dict.addPrecond('free', (obj_name, idi), [])
        for obj_old, obj_new in obj_old_to_new.items():
            content[i] = content[i].replace(obj_old, obj_new)

    
    if not os.path.isdir(os.path.dirname(script_name_out2)):
        os.makedirs(os.path.dirname(script_name_out2))
    with open(script_name_out2, 'w+') as f:
        f.writelines([x+'\n' for x in content])
        num_lines.append(len(content)-4)

    content = precond_dict.printConds() + content
    if not os.path.isdir(os.path.dirname(script_name_out)):
        os.makedirs(os.path.dirname(script_name_out))
    with open(script_name_out, 'w+') as f:
        f.writelines([x+'\n' for x in content])

    json_file = script_name_out.replace('withconds', 'initstate').replace('.txt', '.json')
    if not os.path.isdir(os.path.dirname(json_file)):
        os.makedirs(os.path.dirname(json_file))
    with open(json_file, 'w+') as f:
        f.write(json.dumps(precond_dict.printCondsJSON()))

print(already_grb)
print(len(num_lines))
print(set(not_found))
print(conte)
print('{} scripts, Max Len: {}, Avg Len {}'.format(len(num_lines), np.max(num_lines), np.mean(num_lines)))
