import json
import time
from environment import EnvironmentGraph
from scripts import Script, parse_script_line
from execution import ScriptExecutor


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)


def get_script():
    script_strings = ["[walk] <chair> (1)",
                      "[sit] <chair> (1)"]
    script_lines = [parse_script_line(sl) for sl in script_strings]
    return Script(script_lines)


if __name__ == '__main__':
    graph = load_graph('c:/Work/Python/TestScene6_graph.json')
    script = get_script()
    executor = ScriptExecutor(graph)
    start_time = time.time()
    state_enum = executor.execute(script)
    state = next(state_enum, None)
    end_time = time.time()
    print(state)
    print('Execution time: {}'.format(end_time - start_time))
