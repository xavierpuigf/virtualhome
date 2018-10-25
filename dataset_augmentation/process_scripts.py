# Processes all the scripts
# Same as the backup version but without grabbed precond
import glob
import numpy as np
import script_utils
import os
import json
import pdb
import manual_process
num_lines = []
errors_putback = 0
already_grb = 0
all_scripts = glob.glob('../programs_processed_precond_nograb/withoutconds/*/*.txt')
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

class Precond:
    def __init__(self):
        self.precond_dict = {}

    def addPrecond(self, cond, obj1, obj2):
        if cond not in self.precond_dict.keys():
            self.precond_dict[cond] = {}
        if obj1 not in self.precond_dict[cond]:
            
            self.precond_dict[cond][obj1] = set(obj2)
        else:
            # self.precond_dict[cond][obj1] = set(list(self.precond_dict[cond][obj1])+list(obj2))
            if len(self.precond_dict[cond][obj1]) == 0:
                self.precond_dict[cond][obj1] = set(obj2)
    def printConds(self):
        res = [str(len(self.precond_dict.keys()))]
        for cond in self.precond_dict.keys():
            elem_list = []
            for l in self.precond_dict[cond].keys():

                # if not type(list(self.precond_dict[cond][l])[0]) == tuple:
                #     pdb.set_trace()
                this_str = '{} --> {}'.format(str(l), ' / '.join([str(p) for p in list(self.precond_dict[cond][l])]))
                elem_list.append(this_str)
            elements = ', '.join(elem_list)
            stri = '{}: {}'.format(cond, elements)
            res.append(stri)
        return res

    def printCondsJSON(self):
        conds = []
        for cond in self.precond_dict.keys():
            if cond != 'nearby':
                for it in self.precond_dict[cond].keys():
                    if len(self.precond_dict[cond][it]) > 1:
                        pdb.set_trace()
                    if len(self.precond_dict[cond][it]) == 0:
                        conds.append({cond: it})
                    else:
                        conds.append({cond: [it, list(self.precond_dict[cond][it])[0]]})
        return conds
    def removeCond(self, cond, object_id=None, second=None):
        if object_id is None:
            del self.precond_dict[cond]
        elif second is None:
            del self.precond_dict[cond][object_id]
        else:
            self.precond_dict[cond][object_id].remove(second)
    def obtainCond(self, cond):
        if cond in self.precond_dict.keys():
            return self.precond_dict[cond].keys()
        return []
def insertInstructions(insert_in, content):
    acum = 0
    for insertval in insert_in:
        content.insert(insertval[0]+acum, insertval[1])
        acum += 1
    return content

with open('object_merging_file.txt', 'r') as f:
    lines = f.readlines()
    object_conversion_map = {x.split(':')[0].strip(): x.split(':')[1].strip() for x in lines}

for script_name in all_scripts:
    precond_dict = Precond()
    script_name_in = script_name
    script_name_out = script_name.replace('programs_unprocessed', 'programs_processed_precond_nograb/withconds/')
    script_name_out2 = script_name.replace('programs_unprocessed', 'programs_processed_precond_nograb/withoutconds/')
    with open(script_name, 'r') as f:
        content = [x.strip() for x in f.readlines()]

    if tuple(content) in dict_all_scripts.keys():
        print 'File {} repeated'.format(script_name)
        continue
    dict_all_scripts[tuple(content)] = True
    content = manual_process.manual_process(content, script_name)
    if content is None:
        # Remove file
        continue
    
    # Standarize format, props do not appear
    content[2] = ''
    content[3] = ''

    

    # Correct object names
    for i in range(4, len(content)):
        # Typo: only happens in one example
        content[i] = content[i].replace('PutbBack', 'PutBack')

        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        obj_names_corrected = []
        # Convert the object names
        for obj_name in obj_names:
            try:
                obj_names_corrected.append(object_conversion_map[obj_name.replace('_', ' ')])
            except:
                obj_names_corrected.append(obj_name.replace('_', ' '))
                not_found.append(obj_name)
        obj_names = obj_names_corrected
        content[i] = script_utils.genStrBlock(action, obj_names, ins_num)


    # Remove duplicated grab/switchon/switchoff/open (if they appear right after each other)
    to_remove = []
    for i in range(4, len(content)):
        elem = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(elem)
        if action.upper() in ['GRAB', 'SWITCHON', 'SWITCHOFF', 'CLOSE', 'OPEN']:
            action2, obj_names2, ins_num2 = script_utils.parseStrBlock(content[i-1])
            if action2.upper() == action.upper():
                if obj_names2[0] == obj_names[0] and ins_num[0] == ins_num2[0]:
                    to_remove.append(i)

    for index_i in sorted(to_remove, reverse=True):
        del content[index_i]




    # Check if Object (2) appears before object (1)
    obj_found = {}
    incorrect_found = False
    bad_number = False
    to_repeat = []
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        for l in range(len(obj_names)):
            if obj_names[l] not in obj_found.keys():
                obj_found[obj_names[l]] = 0
            if int(ins_num[l]) > obj_found[obj_names[l]]:
                if int(ins_num[l]) == (obj_found[obj_names[l]]+1):
                    obj_found[obj_names[l]] += 1
                else:
                    # Some people thought that instance number
                    # is instruction number, we will replace the instances by (1)
                    if content[1].split(',')[0].split()[-1].isdigit():
                        content[i].replace(ins_num[l], '1')
                        bad_number = True
                    
                    # In most cases this means that the worker wanted to grab X items
                    else:
                        if action == 'Grab':
                            for it in range(1, int(ins_num[l])):
                                to_repeat.append((i, '[Grab] <{}> ({})'.format(obj_names[l], it)))
                            
                        if action == 'PutBack':
                            for it in range(1, int(ins_num[l])-1):
                                try:
                                    to_repeat.append((i, 
                                        '[PutBack] <{}> ({}) <{}> ({})'.format(obj_names[l], it, obj_names[l+1], ins_num[l+1])))
                                except:
                                    print script_name, content[i]
                            
                        if action == 'PutObjBack':
                            for it in range(1, int(ins_num[l])):
                                to_repeat.append((i, '[PutObjBack] <{}> ({})'.format(obj_names[l], it)))
                            
                        conte += 1
                        #print script_name.split('/')[-1], 'weird numbering', obj_found[obj_names[l]], ins_num[l]
                        #print '\n'.join(content[4:])
                        #print '----\n\n'
                    incorrect_found = True
    if len(to_repeat) > 0:
        content = insertInstructions(to_repeat, content)
    
    if bad_number:
        for ins in range(1, len(content)-3):
            content[1] = content[1].replace(str(ins), '')


    # Check which objects are found, as this cannot be added as precond
    obj_found = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        # If object has not been found add a find
        if len(obj_names) > 0:
            if action.upper() in ['WALK', 'RUN', 'FIND']:
                obj_found[(obj_names[0], ins_num[0])] = True


    # convert type cellphone to text cellphone and touch for type
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action == 'Type' and obj_names[0] != 'KEYBOARD':
            content[i].replace(obj_names[0], 'KEYBOARD')

    # pull faucet and push faucet should be switch on switch off
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action == 'Pull' and obj_names[0] != 'FAUCET':
            content[i].replace('Pull', 'SwitchOn')
        if action == 'Push' and obj_names[0] != 'FAUCET':
            content[i].replace('Pull', 'SwitchOff')

    # cellphone and type
    is_grabbed = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action == 'Type' and obj_names[0] in ['CELLPHONE', 'TELEPHONE']:
            if (obj_names[0], ins_num[0]) in is_grabbed.keys():
                content[i].replace('Touch', 'Type')
            else: print 'should_delete'
        if action in ['Grab', 'Lift']:
            is_grabbed[(obj_names[0], ins_num[0])] = True
        if action in ['PutBack', 'PutObjBack', 'Drop']:
            if (obj_names[0], ins_num[0]) in is_grabbed.keys():
                del is_grabbed[obj_names[0], ins_num[0]]

    # If we have a button and afterwards a switch, remove the button
    all_objects_aux = [script_utils.parseStrBlock(content[i])[1] for i in range(4, len(content))]    
    index_button = [i for i,x in enumerate(all_objects_aux) if len(x) > 0 and x[0] == 'BUTTON']
    to_delete = []
    for bt_ind in index_button:
        if 4+bt_ind < len(content)-1:
            next_act = script_utils.parseStrBlock(content[4+bt_ind+1])
            if next_act[0].startswith('Switch'):
                to_delete.append(4+bt_ind)
                if bt_ind > 0:
                    prev_act = script_utils.parseStrBlock(content[4+bt_ind-1])
                    if prev_act[1][0] == 'BUTTON':
                        to_delete.append(4+bt_ind-1)
    
    for index_i in sorted(to_delete, reverse=True):
        del content[index_i]

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

    # Check for things that are on at the start
    is_on = {}
    nl = 0
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) == 0:
            continue
        obj_id = (obj_names[0], ins_num[0])
        if action == 'SwitchOff':
            if obj_id not in is_on.keys(): # If this light was never switched on/off
                precond_dict.addPrecond('is_on', obj_id, [])
                
            else:
                if not is_on[obj_id]:
                    obj_id = (obj_id[0], str(int(obj_id[1])+1))
                    precond_dict.addPrecond('is_on', obj_id, [])
                    content[i].replace('(1)', '({})'.format(obj_id[1]))
                    nl += 1
            is_on[obj_id] = False
        if action == 'SwitchOn':
            if obj_id in is_on.keys() and is_on[obj_id]:
                obj_id = (obj_id[0], str(int(obj_id[1])+1))
                content[i].replace('(1)', '({})'.format(obj_id[1]))
            elif obj_id not in is_on.keys(): precond_dict.addPrecond('is_off', obj_id, [])
            is_on[obj_id] = True



                

    # Delete push remote control or turn it into switch on if there is no switch
    push_remote = []
    didSwitch = False
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action.upper() == 'PUSH' and obj_names[0].upper() == 'REMOTE CONTROL':
            push_remote.append(i)
        if action.upper().startswith('SWITCH'):
            didSwitch = True
    if len(push_remote) > 0:
        if len(push_remote) == 1:
            if content[0] != 'Change the TV channel':
                if not didSwitch:
                    content[push_remote[0]] = '[SwitchOn] <TELEVISION> (1)'
        
    
    # Convert switch on remote control to switch on television
    for i in range(4, len(content)):
        curr_block = content[i]
        if content[i] == '[SwitchOn] <REMOTE CONTROL> (1)':
            content[i] = '[SwitchOn] <TELEVISION> (1)'


    # Transform lift to grab (if the object was not already grabbed)
    # If the object was already grabbed remove lift
    grabbed = {}
    to_remove = []

    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action.upper()== 'GRAB':
            if (obj_names[0], ins_num[0]) in grabbed.keys() and grabbed[(obj_names[0], ins_num[0])]:
                already_grb +=1
            grabbed[(obj_names[0], ins_num[0])] = True

        if action.upper() in ['PUTBACK', 'PUTOBJBACK', 'DROP'] and (obj_names[0], ins_num[0]) in grabbed.keys() and grabbed[(obj_names[0], ins_num[0])]:
            grabbed[(obj_names[0], ins_num[0])] = False

        # if object was not grabbed and the action is lift, we grab instead
        if action.upper() == 'LIFT':
            if (obj_names[0], ins_num[0]) not in grabbed.keys() or grabbed[(obj_names[0], ins_num[0])] == False:
                content[i] = '[Grab] <{}> ({})'.format(obj_names[0], ins_num[0])
                grabbed[(obj_names[0], ins_num[0])] = True
            else: to_remove.append(i)

    for index_i in sorted(to_remove, reverse=True):
        del content[index_i]


    # transform pour water into <X> to put <x> in sink, grab <x>
    faucet_on = {}
    insert_in = []
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action.upper()== 'SWITCHON' and obj_names[0] == 'FAUCET':
            faucet_on[obj_names[0]] = True
        if action.upper()== 'SWITCHOFF' and obj_names[0] == 'FAUCET':
            try:
                del faucet_on[obj_names[0]]
            except:
                print script_name, 'ERROR'
        if action.upper() == 'POUR' and obj_names[0] == 'WATER' and 'HANDS' not in obj_names[1]:
            if 'FAUCET' in faucet_on.keys():
                content[i] = '[PutBack] <{0}> ({1}) <SINK> (1)'.format(obj_names[1], ins_num[1])
                insert_in.append([i+1, '[Grab] <{0}> ({1})'.format(obj_names[1], ins_num[1])])
    content = insertInstructions(insert_in, content)
            


    # If you put an object in a cabinet/dishwasher make sure you open it first
    # Infer state
    object_open = {}
    open_recipients = ['FRIDGE', 'DISHWASHER', 'CABINET', 'KITCHEN CABINET', 
                       'BATHROOM CABINET', 'CABINET', 'DESK', 'FOLDER', 'CUPBOARD', 
                       'COFFE MAKER', 'OVEN', 'CLOSET', 'DRESSER', 'MICROWAVE', 
                       'FILING CABINET', 'WASHING MACHINE', 'CLOSET', 'CLOSET']
    insert_in = []
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
                print 'Object closed before opening', script_name, object_id
        if action.upper() in ['PUTBACK', 'POUR']:
            try:
                if obj_names[1] in open_recipients:
                    second_object_id = (obj_names[1], ins_num[1])
                    if second_object_id not in object_open.keys():
                        object_open[second_object_id] = True
                        #print script_name, content[1]
                        #pdb.set_trace()
                        insert_in.append([i, '[Open] <{0}> ({1})'.format(second_object_id[0], second_object_id[1])])
            except:
                print content[i], script_name
    
    content = insertInstructions(insert_in, content)

    # If a dishwasher, washing machine is switched on, make sure it is closed first
    insert_in = []
    is_open = {}
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0:
            if obj_names[0] in ['WASHING MACHINE', 'DISHWASHER']:
                if action == 'SwitchOn':
                    if (obj_names[0], ins_num[0]) in is_open.keys() and is_open[(obj_names[0], ins_num[0])]:
                        insert_in.append([i, '[Close] <{}> ({})'.format(obj_names[0], ins_num[0])])
                if action == 'Open':
                    is_open[(obj_names[0], ins_num[0])] = True
                if action == 'Close':
                    is_open[(obj_names[0], ins_num[0])] = False

    content = insertInstructions(insert_in, content)


    # If you read an object make sure you grab it first, unless it was already grabbed
    # Infer state
    insert_in = []
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
        
        if action.upper() in ['READ']:
            if object_id not in object_grabbed.keys(): # it was never put back nor grabbed
                #if object_id not in obj_found.keys(): # it was never found, must be grabbed
                #    precond_dict.addPrecond('grabbed', object_id, [])
                #else:
                val = 1
                insert_in.append([i, '[Grab] <{}> ({})'.format(*object_id)])
            elif not object_grabbed[object_id]: # it was grabbed before, need to grab again
                val = 1
                insert_in.append([i, '[Grab] <{}> ({})'.format(*object_id)])

    content = insertInstructions(insert_in, content)


    # If you putback an object, make sure you grab it first
    # Infer state
    insert_in = []
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
            else: 
                # if it was put back make sure you grab it, otherwise it is initial state (character grabbing it at the beginning)
                if object_id in object_grabbed.keys(): # this means that the objject was grabbed at some point
                    val = 1
                    insert_in.append([i, '[Grab] <{}> ({})'.format(*object_id)])
                else:
                    #if object_id not in obj_found.keys():
                    #    precond_dict.addPrecond('grabbed', object_id, [])
                    #else:
                    if True:
                        # Check the last time the object was found and not put back, if this happened, grab right after find
                        # Otherwise, we just add it right before the interaction
                        index = i
                        if object_id in last_found.keys():
                            index = last_found[object_id]+1
                            if index != i:
                                print script_name
                        val = 1
                        insert_in.append([index, '[Grab] <{}> ({})'.format(*object_id)])
            
            if object_id in last_found.keys(): del last_found[object_id]

    
    content = insertInstructions(insert_in, content)

    # Check objects of interaction while sitting
    is_sitting = None
    obj_location = {}
    object_grabbed = {}
    for k in precond_dict.obtainCond('grabbed'):
        object_grabbed[k] = True
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if action == 'Sit':
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
    # Make sure you walk to find an object before interacting
    # Infer state
    errors_putback += val
    found_object = {}
    insert_in = []
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        # If object has not been found add a find
        if len(obj_names) > 0:
            if action.upper() in ['WALK', 'RUN', 'FIND']:
                found_object[(obj_names[0], ins_num[0])] = True
            #elif action.upper() not in ['PUTOFF']:
            else: # even putoff needs to be found
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
            #else:
            #    # the object has been putoff so no need to find
            #    found_object[(obj_names[0], ins_num[0])] = True
    
    if len(insert_in) > 0: 
        for x in insert_in:
            if x not in precond_dict.obtainCond('inside'):
                precond_dict.addPrecond('nearby', (script_utils.parseStrBlock(x[1])[1][0], script_utils.parseStrBlock(x[1])[2][0]), [])
    content = insertInstructions(insert_in, content)

    # Remove open and close book
    to_remove = []
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        else: 
            continue
        if action.upper() in ['OPEN', 'CLOSE'] and obj_names[0] in ['NOTEBOOK', 'NOVEL', 'BOOK', 'TEXTBOOK', 'ADDRESS BOOK', 'MAGAZINE']:
            to_remove.append(i)

    for index_i in sorted(to_remove, reverse=True):
        del content[index_i]

    # If you put off some clothes that you did not puton, you were wearing them
    for i in range(4, len(content)):
        curr_block = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(curr_block)
        if len(obj_names) > 0: 
            object_id = (obj_names[0], ins_num[0])
        if action.upper == 'PUTOFF':
            if object_id not in puton.keys():
                precond_dict.addPrecond('in', obj_id, [('Character', 1)])
                puton[object_id] = False
            else:    
                if not puton[object_id]:
                    print 'Error, this was already off'


    # Make sure you do not turn to an object if you are grabbing it
    to_remove = []
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
        if action.upper() == 'TURNTO':
            if object_id in object_grabbed.keys():
                to_remove.append(i)
        if action.upper() == 'GRAB':
            object_grabbed[object_id] = True
        
        if action.upper() in ['PUTOBJBACK', 'PUTBACK', 'PUTOFF']:
            try:
                object_grabbed[object_id] = False
            except:
                print 'Error', script_name, object_id
                continue
    for index_i in sorted(to_remove, reverse=True):
        del content[index_i]





    # Remove door
    to_remove = []
    for i in range(4, len(content)):
        elem = content[i]
        action, obj_names, ins_num = script_utils.parseStrBlock(elem)
        if 'DOOR' in obj_names:
            to_remove.append(i)

    for index_i in sorted(to_remove, reverse=True):
        del content[index_i]



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

    if len(content) <= 4:
        print content[0], 'REMOVE TOO SHORT'
        continue


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
            last_open.append(object_id)
            is_open[object_id] = True
        if action.upper() == 'CLOSE': 
            try:
                is_open[object_id] = False
                last_open = [x for x in last_open if x != object_id]
            except:
                if object_id[0] != 'EYES_BOTH':
                    precond_dict.addPrecond('open', object_id, [])

        # If something is not closed, it generally means we are grabbing the staff from it
        if action.upper() == 'GRAB' and len([x for x in is_open.keys() if is_open[x]]) > 0:
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
                            if obj_id[0] in ['DESK', 'TABLE', 'COFFEE TABLE', 'BED', 'SINK', 'CABINET', 'BOOKSHELF', 
                                             'CLOSET', 'BASKET FOR CLOTHES', 'FILING CABINET', 'KITCHEN COUNTER', 'KITCHEN CABINET', 
                                             'BATHROOM CABINET', 'BATHROOM COUNTER', 'CUPBOARD', 'TOOTHBRUSH HOLDER', 'DRESSER'] and len(newobj) < 2:
                                preposition = 'in'
                                if newobj[0][0] == 'CHAIR':
                                    preposition = 'nearby'
                                
                                precond_dict.addPrecond(preposition, newobj[0], [obj_id])
                            else:
                                if obj_id[0] in ['COMPUTER', 'LAPTOP']: continue
                                if newobj[0][0] in ['ARMS_BOTH', 'HAIR', 'FACE']: continue
                                print 'SPATIAL RELATION', i, newobj, obj_id, script_name
        if action == 'Grab':
            obj_id = (obj_names[0], ins_num[0])
            object_grabbed[obj_id] = True



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
    for cond in ['location', 'nearby']:
        for elem in precond_dict.obtainCond(cond):
            if elem in precond_dict.obtainCond('inside'):
                precond_dict.removeCond(cond, elem)
    
    # Good proxy for scripts that are bad (bad AMT workers)
    for i in range(4, len(content)-2):

        action1, obj_names1, ins_num = script_utils.parseStrBlock(content[i])
        action2, obj_names2, ins_num = script_utils.parseStrBlock(content[i+1])
        action3, obj_names3, ins_num = script_utils.parseStrBlock(content[i+2])
        if action1.upper() == 'FIND' and action2.upper() == 'POINTAT' and action3.upper() == 'LOOKAT':            
            if obj_names1[0] == obj_names2[0] and obj_names1[0] == obj_names3[0]:
                print script_name, 'lookat, pointat'  

    
    # Merge names of tasks
    with open('merge_task_name.txt', 'r') as f:
        merge_task = f.readlines()
        merge_task = [(x.split(':')[0].strip(), x.split(':')[1].strip()) for x in merge_task if ':' in x]
        merge_task = {x:y for (x,y) in merge_task}
        task_name = content[0].replace('.','').strip()
        content[0] = task_name
        if content[0].strip() in merge_task.keys():
            content[0] = merge_task[content[0]]
            
    content[0] = (content[0].replace(' a ', ' ').replace(' the ', ' ')
                           .replace(' my ', ' ').replace('I ', ' ').replace('television', 'TV')
                           .replace('tv', 'TV')
                           .replace('Admiring', 'Admire').replace('Completting', 'Complete')
                           .replace('Dinning', 'Dine').replace('Doing', 'Do')
                           .replace('drinking', 'drink').replace('Hanging', 'Hang')
                           .replace('Making', 'Make').replace('Managing', 'Manage').replace('Organizing', 'Organize')
                           .replace('Putting', 'Put').replace('Reading', 'Read').replace('Sending', 'Send').replace('Sewing', 'Sew')
                           .replace('Stretching', 'Stretch').replace('Taking', 'Take').replace('Typing', 'Type').replace('Using', 'Use')
                           .replace('Washing', 'Wash').replace('Wiping', 'Wipe').replace('Writing', 'Write'))
    
    # Standarize task name
    content[0] = content[0][0].upper() + content[0][1:]
    continue
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

print already_grb
print errors_putback
print len(num_lines)
print set(not_found)
print conte
print '{} scripts, Max Len: {}, Avg Len {}'.format(len(num_lines), np.max(num_lines), np.mean(num_lines))
