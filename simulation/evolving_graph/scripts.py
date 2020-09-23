from enum import Enum
import re
import json
from typing import List

from . import common


class Action(Enum):
    """
    All supported actions, value of each enum is a pair (humanized name, required_number of parameters)
    """
    CLOSE = ("Close", 1, [['CAN_OPEN']])
    DRINK = ("Drink", 1, [['DRINKABLE', 'RECIPIENT']])
    FIND = ("Find", 1, [[]])
    WALK = ("Walk", 1, [[]])
    GRAB = ("Grab", 1, [['GRABBABLE']]) # water too
    LOOKAT = ("Look at", 1, [[]])
    LOOKAT_SHORT = ("Look at short", 1, [[]])
    LOOKAT_MEDIUM = LOOKAT
    LOOKAT_LONG = ("Look at long", 1, [[]])
    OPEN = ("Open", 1, [['CAN_OPEN']])
    POINTAT = ("Point at", 1, [[]])
    PUTBACK = ("Put", 2, [['GRABBABLE'], []])
    #PUT = ("Put", 2)
    #PUTBACK = PUT
    PUTIN = ("Put in", 2, [['GRABBABLE'], ['CAN_OPEN']])
    PUTOBJBACK = ("Put back", 1, [[]])
    RUN = ("Run", 1, [[]])
    SIT = ("Sit", 1, [['SITTABLE']])
    STANDUP = ("Stand up", 0)
    SWITCHOFF = ("Switch off", 1, [['HAS_SWITCH']] )
    SWITCHON = ("Switch on", 1, [['HAS_SWITCH']])
    TOUCH = ("Touch", 1, [[]])
    TURNTO = ("Turn to", 1, [[]])
    WATCH = ("Watch", 1, [[]])
    WIPE = ("Wipe", 1, [[]])
    PUTON = ("PutOn", 1, [['CLOTHES']])
    PUTOFF = ("PutOff", 1, [['CLOHES']])
    GREET = ("Greet", 1, [['PERSON']])
    DROP = ("Drop", 1, [[]])
    READ = ("Read", 1, [['READABLE']])
    LIE = ("Lie", 1, [['LIEABLE']])
    POUR = ("Pour", 2, [['POURABLE', 'DRINKABLE'], ['RECIPIENT']])
    TYPE = ("Type", 1, [['HAS_SWITCH']])
    PUSH = ("Push", 1, [['MOVABLE']])
    PULL = ("Pull", 1, [['MOVABLE']])
    MOVE = ("Move", 1, [['MOVABLE']])
    WASH = ("Wash", 1, [[]])
    RINSE = ("Rinse", 1, [[]])
    SCRUB = ("Scrub", 1, [[]])
    SQUEEZE = ("Squeeze", 1, [['CLOTHES']])
    PLUGIN = ("PlugIn", 1, [['HAS_PLUG']])
    PLUGOUT = ("PlugOut", 1, [['HAS_PLUG']])
    CUT = ("Cut", 1, [['EATABLE', 'CUTABLE']])
    EAT = ("Eat", 1, [['EATABLE']]) 
    SLEEP = ("Sleep", 0) 
    WAKEUP = ("WakeUp", 0)
    RELEASE = ("Release", 1, [[]])
    

class ScriptObject(object):

    def __init__(self, name, instance):
        self.name = name.lower().replace(' ', '_')
        self.instance = instance

    def __str__(self):
        return '<{}> ({})'.format(self.name, self.instance)


class ScriptLine(object):

    def __init__(self, action: Action, parameters: List[ScriptObject], index: int):
        self.action = action
        self.parameters = parameters
        self.index = index

    def object(self):
        return self.parameters[0] if len(self.parameters) > 0 else None

    def subject(self):
        return self.parameters[1] if len(self.parameters) > 1 else None

    def __str__(self):
        return '[{}]'.format(self.action.name) + ''.join([' ' + str(par) for par in self.parameters]) + ' [{}]'.format(self.index)


class Script(object):

    def __init__(self, script_lines: List[ScriptLine]):
        self._script_lines = script_lines

    def __len__(self):
        return len(self._script_lines)

    def __getitem__(self, item):
        return self._script_lines[item]

    def obtain_objects(self):
        list_objects = []
        for script_line in self._script_lines:
            for parameter in script_line.parameters:
                list_objects.append((parameter.name, parameter.instance))
        return list(set(list_objects))

    def from_index(self, index):
        return Script(self._script_lines[index:])


class ScriptParseException(common.Error):
    pass


def parse_script_line(string, index):
    """
    :param string: script line in format [action] <object> (object_instance) <subject> (object_instance)
    :return: ScriptLine objects; raises ScriptParseException
    """
    params = []

    patt_action = r'^\[(\w+)\]'
    patt_params = r'\<(.+?)\>\s*\((.+?)\)'

    action_match = re.search(patt_action, string.strip())
    if not action_match:
        raise ScriptParseException('Cannot parse action')
    action_string = action_match.group(1).upper()
    if action_string not in Action.__members__:
        raise ScriptParseException('Unknown action "{}"', action_string)
    action = Action[action_string]

    param_match = re.search(patt_params, action_match.string[action_match.end(1):])
    while param_match:
        params.append(ScriptObject(param_match.group(1), int(param_match.group(2))))
        param_match = re.search(patt_params, param_match.string[param_match.end(2):])

    if len(params) != action.value[1]:
        raise ScriptParseException('Wrong number of parameters for "{}". Got {}, expected {}',
                                   action.name, len(params), action.value[1])

    return ScriptLine(action, params, index)


def script_to_list_string(script):
    list_string = []
    for script_line in script:
        st = str(script_line)
        st = ' '.join(st.split()[:-1])
        list_string.append(st)
    return list_string


def script_to_string(script):
    list_string = print_script_to_list_string(script)
    return ', ',join(list_string)


def read_script(file_name):
    script_lines = []
    with open(file_name) as f:
        index = 1
        for line in f:
            if '[' not in line:
                continue
            line = line.strip()
            
            if len(line) > 0 and not line.startswith('#'):
                script_lines.append(parse_script_line(line, index))
                index += 1
    return Script(script_lines)


def read_script_from_list_string(list_string):
    script_lines = []
    f = list_string
    index = 1
    for line in f:
        if '[' not in line:
            continue
        line = line.strip()
        
        if len(line) > 0 and not line.startswith('#'):
            script_lines.append(parse_script_line(line, index))
            index += 1
    return Script(script_lines)


def read_script_from_string(string):

    script_lines = []
    string = string.split(', ')
    index = 1
    for line in string:
        if '[' not in line:
            continue
        line = line.strip()
        
        if len(line) > 0 and not line.startswith('#'):
            script_lines.append(parse_script_line(line, index))
            index += 1
    return Script(script_lines)
