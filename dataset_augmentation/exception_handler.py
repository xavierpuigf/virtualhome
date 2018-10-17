from enum import Enum
from utils_preconds import *
import script_utils
from termcolor import colored

# class ProgramState():

#     def first_precond(self, preconds):
#         precond = Precond()
#         for elem in preconds:
#             precond_name = list(elem)[0]
#             precond_obj = elem[precond_name]
#             print(type(precond_name), precond_obj[0], precond_obj[1])
#             precond.addPrecond(precond_name, tuple(precond_obj[0]), tuple(precond_obj[1]))
#         return precond

#     def __init__(self, program, preconds):
#         self.program = program
#         self.preconds = preconds
#         self.state_timestep = [self.first_precond(preconds)]
#         self.get_state_per_timestep()
        
#     def evolve_state(self, prev_state, action, object1, object2):
#         new_state = prev_state.copy()
#         if action == 'SWITCHOFF':
#             return None

#     def get_state_per_timestep(self):
#         prev_cond = self.state_timestep[0]
#         for elem in self.program:
#             action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])
#             action = action.upper()
#             obj1, obj2 = None, None
#             if len(objects) > 1:
#                 obj1 = tuple(objects[0], ids[0])
#             if len(objects) > 2:
#                 obj2 = tuple(objects[1], ids[1])

#             newcond = self.evolve_state(prev_cond, action, obj1, obj2)
#             self.state_timestep.append(newcond)
#             prev_cond = newcond



class ProgramException(Enum):
    NOT_CLOSED = 1
    NOT_OPEN = 2
    NOT_SITTING = 3
    NOT_LYING = 4
    NOT_CLOSE = 5
    NOT_FACING = 6
    SITTING = 7

message_to_exception = {
    'is not closed': ProgramException.NOT_CLOSED,
    'is not sitting': ProgramException.NOT_SITTING,
    'is sitting': ProgramException.SITTING,
    'is not lying': ProgramException.NOT_LYING,
    'is not lying or sitting': ProgramException.NOT_SITTING,
    'is not close to': ProgramException.NOT_CLOSE,
    'is not facing': ProgramException.NOT_FACING
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
    print('Correct exception {}'.format(exception_str))
    instructions_program = input_program[4:]
    program_header = input_program[:4]
    try:
        line_exception, exception = parseException(exception_str)
    except:
        printProgramWithLine(instructions_program)
        return None
    

    #printProgramWithLine(instructions_program, [line_exception])
    
    #program = ProgramState(input_program, init_state)
    
    corrected_instructions = None
    insert_in = []
    if exception == ProgramException.NOT_CLOSED:
        corrected_instructions = removeInstructions([line_exception], instructions_program)
    
    if exception == ProgramException.NOT_SITTING:
        corrected_instructions = removeInstructions([line_exception], instructions_program)
    
    if exception == ProgramException.NOT_LYING:
        corrected_instructions = removeInstructions([line_exception], instructions_program)

    if exception == ProgramException.NOT_CLOSE:
        action, objects, ids = script_utils.parseStrBlock(instructions_program[line_exception])       
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

    #print('\n')
    #print(colored('Corrected', 'green'))
    #printProgramWithLine(corrected_instructions)
    output_program = program_header + corrected_instructions

    return output_program