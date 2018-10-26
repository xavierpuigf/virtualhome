from enum import Enum
from utils_preconds import *
import script_utils
from termcolor import colored


actions_2_object =  ['PUTBACK', 'POUR', 'THROW', 'COVER', 'WRAP', 'SOAK', 'SPREAD']


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

message_to_exception = {
    'is not closed': ProgramException.NOT_CLOSED,
    'is not sitting': ProgramException.NOT_SITTING,
    'is sitting': ProgramException.SITTING,
    'is not lying': ProgramException.NOT_LYING,
    'is not lying or sitting': ProgramException.NOT_SITTING,
    'is not close to': ProgramException.NOT_CLOSE,
    'is not facing': ProgramException.NOT_FACING,
    'is not off': ProgramException.NOT_OFF,
    'is not on': ProgramException.NOT_ON,
    'is not plugged_out': ProgramException.NOT_PLUGGED_OUT,
    'is unplugged': ProgramException.UNPLUGGED,
    'many things on': ProgramException.OCCUPIED,
    'on the': ProgramException.OCCUPIED,
    'is still on': ProgramException.STILL_ON,
    'between and is closed': ProgramException.DOOR_CLOSED
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
    exception_name = split_exception[2]
    exception_split = exception_name.split('when executing')
    exception_name = exception_split[0]
    
    instruction = exception_split[1][1:-1]

    exception_name = exception_name.split()[2:]
    argument = [x for x in exception_name if ')' in x]
    
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
    print('--')
    print(id_env)
    print(id_mapping)
    # Given an object name and an id in the environment returns a script id
    object_name = object_name.lower().replace(' ', '_')
    cont_object = 0
    for elem, id_en in id_mapping.items():
        if id_en == id_env:
            return int(elem[1])
        if elem[0] == object_name:
            cont_object += 1
    
    # update the script2env mapping
    id_object = cont_object + 1
    id_mapping[(object_name, id_object)] = id_env
    print(id_mapping)
    print('!!!')
    return id_object

def correctedProgram(input_program, init_state, final_state, exception_str, verbose=True, id_mapping={}):
    #print('Correct exception {}'.format(exception_str))
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
    if exception == ProgramException.NOT_CLOSED:
        corrected_instructions = removeInstructions([line_exception], instructions_program)
    
    if exception == ProgramException.NOT_SITTING:
        corrected_instructions = removeInstructions([line_exception], instructions_program)
    
    if exception == ProgramException.NOT_LYING:
        corrected_instructions = removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_CLOSE:
        action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])
        if action.upper() in  actions_2_object:
            insert_in.append([line_exception, '[Walk] <{}> ({})'.format(objects[1], ids[1])])

        else:      
            insert_in.append([line_exception, '[Walk] <{}> ({})'.format(objects[0], ids[0])])
        
        corrected_instructions = insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.NOT_FACING:
        action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])
        insert_in.append([line_exception, '[TurnTo] <{}> ({})'.format(objects[0], ids[0])])           
        corrected_instructions = insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.SITTING:
        action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])
        insert_in.append([line_exception, '[StandUp]'])      
        corrected_instructions = insertInstructions(insert_in, instructions_program)
        
        #printProgramWithLine(corrected_instructions)     

    if exception == ProgramException.NOT_OFF:
        corrected_instructions = removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_OFF:
        corrected_instructions = removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_PLUGGED_OUT:
        corrected_instructions = removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.STILL_ON:
        # TODO: check that we are actually switching it on afterwards
        action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])
        insert_in.append(
                [line_exception, '[SwitchOff] <{}> ({})'.format(objects[0], ids[0])])           
        corrected_instructions = insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.UNPLUGGED:
        action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])
        insert_in.append(
                [line_exception, '[PlugIn] <{}> ({})'.format(objects[0], ids[0])])           
        corrected_instructions = insertInstructions(insert_in, instructions_program)

    if exception == ProgramException.DOOR_CLOSED:
        pdb.set_trace()
        object_name = 'Door'
        id_object_env = argument_exception[0][1]
        id_object = getidperobject(object_name, id_object_env, id_mapping)
        insert_in.append([line_exception, '[Walk] <{}> ({})'.format(object_name, id_object)])
        insert_in.append([line_exception, '[Find] <{}> ({})'.format(object_name, id_object)])
        insert_in.append([line_exception, '[Open] <{}> ({})'.format(object_name, id_object)])
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
            id_object_env = object_occupied['id']
            id_object = getidperobject(object_name, id_object_env,id_mapping)
            print('newidenv', id_object_env)
           
            # TODO: we may want to pick objects with 2 hands
            insert_in.append([line_exception, '[Find] <{}> ({})'.format(object_name, id_object)])
            insert_in.append([line_exception, '[Grab] <{}> ({})'.format(object_name, id_object)])
            insert_in.append([line_exception, '[Release] <{}> ({})'.format(object_name, id_object)])
        corrected_instructions = insertInstructions(insert_in, instructions_program)
        #corrected_instructions = removeInstructions([line_exception], instructions_program)

    #print('\n')
    #print(colored('Corrected', 'green'))
    #printProgramWithLine(corrected_instructions)
    output_program = program_header + corrected_instructions
    print(id_mapping)
    return output_program
