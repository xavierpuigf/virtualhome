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
    'is not plugged_out': ProgramException.NOT_PLUGGED_OUT
}

def printProgramWithLine(program, lines=[]):
    for it, elem in enumerate(program):
        if it in lines:
            char = '*'
        else:
            char = ' '
        print('{}  {}'.format(char, elem))

def parseException(exception_str):
    split_exception = exception_str.split(',')
    exception_name = split_exception[2]
    exception_split = exception_name.split('when executing')
    exception_name = exception_split[0]
    
    instruction = exception_split[1][1:-1]

    exception_name = exception_name.split()[2:]
    exception_name = [x for x in exception_name if ')' not in x]
    exception_name = ' '.join(exception_name)
    line_number = int(instruction.split()[-1][1:-1])-1

    if exception_name in message_to_exception.keys():
        return line_number, message_to_exception[exception_name]

    else:
        print(colored('Exception "{}" not found'.format(exception_name), 'red'))
        raise ValueError

    return None

def correctedProgram(input_program, init_state, exception_str):
    #print('Correct exception {}'.format(exception_str))
    instructions_program = input_program[4:]
    program_header = input_program[:4]
    try:
        line_exception, exception = parseException(exception_str)
    except:
        printProgramWithLine(instructions_program)
        return None
    

    #printProgramWithLine(instructions_program, [line_exception])
    
    #program = ProgramState(input_program, init_state)
    
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

    #print('\n')
    #print(colored('Corrected', 'green'))
    #printProgramWithLine(corrected_instructions)
    output_program = program_header + corrected_instructions

    return output_program