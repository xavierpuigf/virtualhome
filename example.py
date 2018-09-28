import utils
from execution import Relation
from scripts import read_script
from execution import ScriptExecutor
from preparation import AddMissingScriptObjects, AddRandomObjects, ChangeObjectStates


def print_node_names(n_list):
    if len(n_list) > 0:
        print([n.class_name for n in n_list])


def example_1():
    print('Example 1')
    print('---------')
    graph = utils.load_graph('example_graphs/TestScene6_graph.json')
    name_equivalence = utils.load_name_equivalence()
    script = read_script('example_scripts/example_script_1.txt')
    executor = ScriptExecutor(graph, name_equivalence)
    state_enum = executor.execute(script)
    state = next(state_enum, None)
    if state is None:
        print('Script is not executable.')
    else:
        print('Script is executable')
        fridge_nodes = state.get_nodes_by_attr('class_name', 'microwave')
        if len(fridge_nodes) > 0:
            print("Microwave states are:", fridge_nodes[0].states)
        chars = state.get_nodes_by_attr('class_name', 'character')
        if len(chars) > 0:
            char = chars[0]
            print("Character holds:")
            print_node_names(state.get_nodes_from(char, Relation.HOLDS_RH))
            print_node_names(state.get_nodes_from(char, Relation.HOLDS_LH))
            print("Character is on:")
            print_node_names(state.get_nodes_from(char, Relation.ON))
            print("Character is in:")
            print_node_names(state.get_nodes_from(char, Relation.INSIDE))
            print("Character states are:", char.states)


def example_2():
    print()
    print('Example 2')
    print('---------')
    graph = utils.load_graph('example_graphs/TestScene6_graph.json')
    script = read_script('example_scripts/example_script_2.txt')
    name_equivalence = utils.load_name_equivalence()
    object_placing = utils.load_object_placing()
    properties_data = utils.load_properties_data()
    executor = ScriptExecutor(graph, name_equivalence)

    # Execute script; fails due to a missing object
    state_enum = executor.execute(script)
    state = next(state_enum, None)
    print('Script is {0}executable'.format('not ' if state is None else ''))

    # Add missing objects (random)
    prepare_1 = AddMissingScriptObjects(name_equivalence, properties_data, object_placing)

    # Add 10 random objects
    prepare_2 = AddRandomObjects(properties_data, object_placing, choices=10)

    # Change states of "can_open" and "has_switch" objects to
    # open/closed, on/off)
    prepare_3 = ChangeObjectStates(properties_data)

    state_enum = executor.execute(script, [prepare_1, prepare_2, prepare_3])
    state = next(state_enum, None)
    print('Script is {0}executable'.format('not ' if state is None else ''))


if __name__ == '__main__':
    example_1()
    example_2()