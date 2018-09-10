import json
from common import TimeMeasurement
from environment import EnvironmentGraph
from scripts import Script, parse_script_line
from execution import ScriptExecutor


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)


def get_script():
    script0_strings = ['[walk] <chair> (1)',
                       '[sit] <chair> (1)']
    script1_strings = ['[walk] <waterglass> (1)',
                       '[grab] <waterglass> (1)',
                       #'[find] <plate> (1)',
                       #'[grab] <plate> (1)',
                       '[walk] <fridge> (1)',
                       '[open] <fridge> (1)',
                       '[putin] <waterglass> (1) <fridge> (1)',
                       '[close] <fridge> (1)']
    script_strings = ['[walk] <kitchen_table> (1)',
                      '[find] <bench> (1)',
                      '[sit] <bench> (1)',
                      ]

    script_lines = [parse_script_line(sl) for sl in script_strings]
    return Script(script_lines)


if __name__ == '__main__':
    graph = load_graph('c:/Work/Python/TestScene6_graph.json')
    script = get_script()
    executor = ScriptExecutor(graph)
    tm = TimeMeasurement.start('Execution')
    state_enum = executor.execute(script)
    state = next(state_enum, None)
    TimeMeasurement.stop(tm)
    print(state)
    print('Measurements:\n' + TimeMeasurement.result_string())
