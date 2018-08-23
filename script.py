from enum import Enum
import re


class Action(Enum):
    """
    All supported actions, value of each enum is a pair (humanized name, required_number of parameters)
    """
    CLOSE = ("Close", 1)
    DRINK = ("Drink", 1)
    FIND = ("Find", 1)
    GOTO = ("Walk", 1)
    GRAB = ("Grab", 1)
    LOOKAT = ("Look at", 1)
    LOOKAT_SHORT = ("Look at short", 1)
    LOOKAT_MEDIUM = LOOKAT
    LOOKAT_LONG = ("Look at long", 1)
    OPEN = ("Open", 1)
    POINTAT = ("Point at", 1)
    PUT = ("Put", 2)
    PUTBACK = PUT
    PUTIN = ("Put in", 2)
    PUTOBJBACK = ("Put back", 1)
    RUN = ("Run", 1)
    SIT = ("Sit", 1)
    STANDUP = ("Stand up", 0)
    SWITCHOFF = ("Switch off", 1)
    SWITCHON = ("Switch on", 1)
    TOUCH = ("Touch", 1)
    TURNTO = ("Turn to", 1)
    WALK = GOTO
    WATCH = ("Watch", 1)


class ScriptObject(object):

    def __init__(self, name, instance):
        self.name = name.lower()
        self.instance = instance

    def __str__(self):
        return '<{}> ({})'.format(self.name, self.instance)


class ScriptLine(object):

    def __init__(self, action, parameters):
        self.action = action
        self._parameters = parameters

    def object(self):
        return self._parameters[0]

    def subject(self):
        return self._parameters[1]


class ScriptParseException(Exception):
    def __init__(self, message, *args):
        self.message = message.format(*args)

    def __str__(self):
        return self.message


def parse_script_line(string):
    """
    :param string: script line in format [action] <object> (object_instance) <subject> (object_instance)
    :return: ScriptLine objects; raises ScriptParseException
    """
    params = []

    patt_action = r'^\[(\w+)\]'
    patt_params = r'<([\w\s]+)>\s*\((\d+)\)'

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

    return ScriptLine(action, params)





