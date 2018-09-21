import utils
from common import TimeMeasurement
from scripts import read_script
from execution import ScriptExecutor


if __name__ == '__main__':
    graph = utils.load_graph('example_graphs/TestScene6_graph.json')
    name_equivalence = utils.load_name_equivalence()
    script = read_script('example_scripts/script_test_000003.txt')
    executor = ScriptExecutor(graph, name_equivalence)
    tm = TimeMeasurement.start('Execution')
    state_enum = executor.execute(script)
    state = next(state_enum, None)
    TimeMeasurement.stop(tm)
    print(state)
    print('Measurements:\n' + TimeMeasurement.result_string())
