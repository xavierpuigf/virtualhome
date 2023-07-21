from enum import Enum
#from utils_preconds import *
import augmentation_utils
from termcolor import colored
import ipdb
import random
actions_2_object = ['PUTBACK', 'POUR', 'THROW', 'COVER', 'WRAP', 'SOAK', 'SPREAD']


class ProgramException(Enum):
    NOT_CLOSED = 1
    NOT_OPEN = 2
    NOT_SITTING = 3
    NOT_LYING = 4
    NOT_CLOSE = 5
    NOT_FACING = 6
    SITTING = 7
    NOT_OFF = 8
    NOT_ON = 9
    NOT_PLUGGED_OUT = 10
    OCCUPIED = 11
    UNPLUGGED = 12
    STILL_ON = 13
    DOOR_CLOSED = 14
    INSIDE_CLOSED = 15
    FREE_HAND = 16


message_to_exception = {
    'is not closed': ProgramException.NOT_CLOSED,
    'is not sitting': ProgramException.NOT_SITTING,
    'is sitting': ProgramException.SITTING,
    'is not lying': ProgramException.NOT_LYING,
    'is not lying or sitting': ProgramException.NOT_SITTING,
    'is not close to': ProgramException.NOT_CLOSE,
    'is not facing': ProgramException.NOT_FACING,
    'does not face': ProgramException.NOT_FACING,
    'is not off': ProgramException.NOT_OFF,
    'is not on': ProgramException.NOT_ON,
    'is not plugged_out': ProgramException.NOT_PLUGGED_OUT,
    'is unplugged': ProgramException.UNPLUGGED,
    'many things on': ProgramException.OCCUPIED,
    'on the': ProgramException.OCCUPIED,
    'is still on': ProgramException.STILL_ON,
    'between and is closed': ProgramException.DOOR_CLOSED,
    'is inside other closed thing':  ProgramException.INSIDE_CLOSED,
    'does not have a free hand': ProgramException.FREE_HAND
}


def printProgramWithLine(program, lines=[]):
    for it, elem in enumerate(program):
        if it in lines:
            char = '*'
        else:
            char = ' '
        print('{}  {}'.format(char, elem))


def parseException(exception_str, verbose=True):
    split_exception = exception_str.replace('> (', '>(').split(',')
    exception_name = ' '.join(split_exception[1:])
    exception_split = exception_name.split('when executing')
    exception_name = exception_split[0]
    try:
        instruction = exception_split[1][1:-1]
    except:
        pdb.set_trace()


    exception_name = exception_name.split()[2:]
    argument = [x for x in exception_name if '>(' in x]
    
    for it_arg, argu in enumerate(argument):
        obji = argu.split('>')[0][1:]
        idi = argu.split('(')[1][:-1]
        argument[it_arg] = (obji, idi)
    exception_name = [x for x in exception_name if ')' not in x]
    exception_name = ' '.join(exception_name)

    line_number = int(instruction.split()[-1][1:-1])-1

    if exception_name in message_to_exception.keys():
        return line_number, message_to_exception[exception_name], argument

    else:
        if verbose:
            print(colored('Exception "{}" not found'.format(exception_name), 'red'))
            print(colored(exception_str, 'blue'))
            
        raise ValueError

    return None


def getidperobject(object_name, id_env, id_mapping):
    # Given an object name and an id in the environment returns a script id
    object_name = object_name.lower().replace(' ex', '_')
    cont_object = 0
    for elem, id_en in id_mapping.items():
        if id_en == int(id_env):
            if object_name == 'door':
                raise ValueError
            return int(elem[1])
        if elem[0] == object_name:
            cont_object += 1
    
    # update the script2env mapping
    id_object = cont_object + 1
    id_mapping[(object_name, id_object)] = int(id_env)
    return id_object


def correctedProgram(input_program, init_state, final_state, exception_str, verbose=True, id_mapping={}):
    instructions_program = input_program[4:]
    program_header = input_program[:4]
    try:
        line_exception, exception, argument_exception = parseException(exception_str, verbose)
    except ValueError:
        print(exception_str)
        if verbose:
            printProgramWithLine(instructions_program)
        return (None, exception_str)

    corrected_instructions = instructions_program
    insert_in = []
    action, objects, ids = augmentation_utils.parseStrBlock(instructions_program[line_exception])
    if exception == ProgramException.NOT_CLOSED: 
        if action.upper() != 'OPEN':
            insert_in.append([line_exception, '[Close] <{}> ({})'.format(objects[0], ids[0])]) 
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
            ipdb.set_trace()
        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_OPEN:
        if action.upper() != 'CLOSE':
            insert_in.append([line_exception, '[Open] <{}> ({})'.format(objects[0], ids[0])]) 
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
            ipdb.set_trace()
        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)
    
    if exception == ProgramException.NOT_SITTING:
        if action.upper() != 'STANDUP':
            if action.upper() in ['SLEEP', 'WAKEUP']:
                return (None, exception_str)
            insert_in.append([line_exception, '[Sit] <{}> ({})'.format(objects[0], ids[0])]) 
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)
    
    if exception == ProgramException.NOT_LYING:
        if action.upper() != 'STANDUP':
            if action.upper() in ['SLEEP', 'WAKEUP']:
                return (None, exception_str)
            insert_in.append([line_exception, '[Lie] <{}> ({})'.format(objects[0], ids[0])])
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_CLOSE:
        object_name, id_object_env = argument_exception[0]
        id_object = getidperobject(object_name, id_object_env, id_mapping)
        insert_in.append([line_exception, '[Walk] <{}> ({})'.format(object_name, id_object)]) 
        corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.NOT_FACING:
        insert_in.append([line_exception, '[TurnTo] <{}> ({})'.format(objects[0], ids[0])])           
        corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.SITTING:
        if action.upper() == 'SIT':
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)
            ipdb.set_trace()
        else:
            insert_in.append([line_exception, '[StandUp]'])      
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.NOT_ON:
        if action.upper() != 'SWITCHOFF':
            insert_in.append([line_exception, '[SwitchOn] <{}> ({})'.format(objects[0], ids[0])]) 
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
            ipdb.set_trace()
        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_OFF:
        if action.upper() != 'SWITCHON':
            insert_in.append([line_exception, '[SwitchOff] <{}> ({})'.format(objects[0], ids[0])]) 
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
            ipdb.set_trace()
        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_PLUGGED_OUT:
        if action.upper() != 'PLUGIN':
            insert_in.append([line_exception, '[PlugOut] <{}> ({})'.format(objects[0], ids[0])]) 
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
            ipdb.set_trace()
        else:
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.STILL_ON:
        action, objects, ids = augmentation_utils.parseStrBlock(instructions_program[line_exception])
        insert_in.append(
                [line_exception, '[SwitchOff] <{}> ({})'.format(objects[0], ids[0])])           
        corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.UNPLUGGED:
        if action.upper() == 'PLUGOUT':
            corrected_instructions = augmentation_utils.removeInstructions([line_exception], instructions_program)
        else:
            insert_in.append(
                    [line_exception, '[PlugIn] <{}> ({})'.format(objects[0], ids[0])])           
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.DOOR_CLOSED:
        door_argument = [arg for arg in argument_exception if arg[0] == 'door']
        id_object_env = door_argument[-1][1]
        object_name = 'door'
        try:
            id_object = getidperobject(object_name, id_object_env, id_mapping)
        except:
            print('Door used')
            print('Previous program')

        insert_in.append([line_exception, '[Walk] <{}> ({})'.format(object_name, id_object)])
        insert_in.append([line_exception, '[Find] <{}> ({})'.format(object_name, id_object)])
        insert_in.append([line_exception, '[Open] <{}> ({})'.format(object_name, id_object)])
        corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.OCCUPIED:
        node_state_dict = final_state.to_dict()['nodes']
        edge_state_dict = final_state.to_dict()['edges']
        edge_interest = [edge_graph['from_id'] for edge_graph in edge_state_dict 
                if (edge_graph['to_id'] == int(argument_exception[0][1]) 
                    and edge_graph['relation_type'] in ['ON'])]
        node_interest = [node_graph for node_graph in node_state_dict if node_graph['id'] in edge_interest]

        # assumption: all the objects did not appear in the program before
        prev_obj = {}
        for object_script in list(final_state._script_objects):
            ob_mod = object_script[0]
            if ob_mod not in prev_obj:
                prev_obj[ob_mod] = 1
            else:
                prev_obj[ob_mod] += 1
        for object_occupied in node_interest:
            object_name = object_occupied['class_name']
            if object_name == 'character':
                continue
            id_object_env = object_occupied['id']
            id_object = getidperobject(object_name, id_object_env,id_mapping)
            insert_in.append([line_exception, '[Find] <{}> ({})'.format(object_name, id_object)])
            insert_in.append([line_exception, '[Grab] <{}> ({})'.format(object_name, id_object)])
            insert_in.append([line_exception, '[Release] <{}> ({})'.format(object_name, id_object)])
        corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
    
    if exception == ProgramException.INSIDE_CLOSED:
        node_state_dict = final_state.to_dict()['nodes']
        edge_state_dict = final_state.to_dict()['edges']
        id_object_env = id_mapping[(objects[0], int(ids[0]))]
        
        edge_interest = [edge_graph['to_id'] for edge_graph in edge_state_dict if (edge_graph['from_id'] == id_object_env
                    and edge_graph['relation_type'] in ['INSIDE'])]
        
        node_interest = [node_graph for node_graph in node_state_dict if node_graph['id'] in edge_interest]
        return (None, exception_str)

    if exception == ProgramException.FREE_HAND:
        if action.upper() != 'GRAB':
            node_state_dict = final_state.to_dict()['nodes']
            edge_state_dict = final_state.to_dict()['edges']
            edge_graph_grabbed = [edge_graph['to_id'] for edge_graph in edge_state_dict if 'holds_lh' in edge_graph['relation_type'].lower()]
            edge_graph_grabbed += [edge_graph['to_id'] for edge_graph in edge_state_dict if 'holds_rh' in edge_graph['relation_type'].lower()]
            elem = random.randrange(len(edge_graph_grabbed))
            edge_interest = edge_graph_grabbed[elem]
            node_interest = [node_graph for node_graph in node_state_dict if node_graph['id'] == edge_interest][0]
            id_object_env = node_interest['id']
            object_name = node_interest['class_name']
            id_object = getidperobject(node_interest['class_name'], node_interest['id'] ,id_mapping) 
            insert_in.append([line_exception, '[Release] <{}> ({})'.format(object_name, id_object)])
            insert_in.append([line_exception+1, '[Grab] <{}> ({})'.format(object_name, id_object)])
            corrected_instructions = augmentation_utils.insertInstructions(insert_in, instructions_program)
        else:
            return (None, exception_str)

    output_program = program_header + corrected_instructions
    return output_program
