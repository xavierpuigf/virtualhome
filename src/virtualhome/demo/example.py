import json
import sys
sys.path.append('../simulation')
import evolving_graph.utils as utils
from evolving_graph.execution import Relation, State
from evolving_graph.scripts import read_script
from evolving_graph.execution import ScriptExecutor
from evolving_graph.environment import EnvironmentGraph
from evolving_graph.preparation import AddMissingScriptObjects, AddRandomObjects, ChangeObjectStates, \
    StatePrepare, AddObject, ChangeState, Destination


def print_node_names(n_list):
    if len(n_list) > 0:
        print([n.class_name for n in n_list])


def example_1():
    print('Example 1')
    print('---------')
    graph = utils.load_graph('../example_graphs/TestScene6_graph.json')
    name_equivalence = utils.load_name_equivalence()
    script = read_script('example_scripts/example_script_1.txt')
    executor = ScriptExecutor(graph, name_equivalence)
    state_enum = executor.find_solutions(script)
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
    graph = utils.load_graph('../example_graphs/TestScene6_graph.json')
    script = read_script('example_scripts/example_script_2.txt')
    name_equivalence = utils.load_name_equivalence()
    object_placing = utils.load_object_placing()
    properties_data = utils.load_properties_data()
    executor = ScriptExecutor(graph, name_equivalence)

    # Execute script; fails due to a missing object
    state_enum = executor.find_solutions(script)
    state = next(state_enum, None)
    print('Script is {0}executable'.format('not ' if state is None else ''))

    # Add missing objects (random)
    prepare_1 = AddMissingScriptObjects(name_equivalence, properties_data, object_placing)

    # Add 10 random objects
    prepare_2 = AddRandomObjects(properties_data, object_placing, choices=10)

    # Change states of "can_open" and "has_switch" objects to
    # open/closed, on/off)
    prepare_3 = ChangeObjectStates(properties_data)

    state_enum = executor.find_solutions(script, [prepare_1, prepare_2, prepare_3])
    state = next(state_enum, None)
    print('Script is {0}executable'.format('not ' if state is None else ''))


def example_3():
    print()
    print('Example 3')
    print('---------')
    graph = utils.load_graph('../example_graphs/TestScene6_graph.json')
    script = read_script('example_scripts/example_script_2.txt')
    name_equivalence = utils.load_name_equivalence()
    properties_data = utils.load_properties_data()
    executor = ScriptExecutor(graph, name_equivalence)

    # "Manual" changes:
    # * add object named kettle to a stove
    # * add a vacummcleaner on the floor in the livingroom and turn it on
    # * turn on all lights (lightswitches)
    prepare_1 = StatePrepare(properties_data,
                             [AddObject('kettle', Destination.on('stove')),
                              AddObject('vacuumcleaner', Destination.on('floor', 'livingroom'), [State.ON]),
                              ChangeState('lightswitch', [State.ON])])
    state_enum = executor.find_solutions(script, [prepare_1])
    state = next(state_enum, None)
    print('Script is {0}executable'.format('not ' if state is None else ''))


def example_4():
    print()
    print('Example 4')
    print('---------')
    graph = utils.load_graph('../example_graphs/TestScene6_graph.json')
    script = read_script('example_scripts/example_script_3.txt')
    name_equivalence = utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    state = executor.execute(script)
    if state is None:
        print('Script is not executable, since {}'.format(executor.info.get_error_string()))
    else:
        print('Script is executable')


def example_5():

    properties_data = utils.load_properties_data()
    object_states = utils.load_object_states()
    object_placing = utils.load_object_placing()
    graph_dict = {
            'nodes': [
                {"id": 1, 'class_name': "kitchen", "category": "Rooms", "properties": [], "states": []},
                {"id": 2, 'class_name': "bedroom", "category": "Rooms", "properties": [], "states": []},
                {"id": 3, 'class_name': "home_office", "category": "Rooms", "properties": [], "states": []},
                {"id": 4, 'class_name': "bathroom", "category": "Rooms", "properties": [], "states": []},
                {"id": 5, 'class_name': "character", "category": "", "properties": [], "states": []},
                {"id": 6, 'class_name': "door", "category": "", "properties": ["CAN_OPEN"], "states": ["OPEN"]},
                {"id": 7, 'class_name': "door", "category": "", "properties": ["CAN_OPEN"], "states": ["OPEN"]},
                {"id": 8, 'class_name': "door", "category": "", "properties": ["CAN_OPEN"], "states": ["OPEN"]},
            ],
            'edges': [
                {"from_id": 5, "to_id": 2, "relation_type": "INSIDE"},
                {"from_id": 6, "to_id": 1, "relation_type": "BETWEEN"},
                {"from_id": 6, "to_id": 2, "relation_type": "BETWEEN"},
                {"from_id": 7, "to_id": 1, "relation_type": "BETWEEN"},
                {"from_id": 7, "to_id": 3, "relation_type": "BETWEEN"},
                {"from_id": 8, "to_id": 3, "relation_type": "BETWEEN"},
                {"from_id": 8, "to_id": 4, "relation_type": "BETWEEN"},
            ]}

    helper = utils.graph_dict_helper(properties_data, object_placing, object_states, max_nodes=15)
    helper.initialize(graph_dict)

    print()
    print('Example 5')
    print('---------')
    script = read_script('example_scripts/example_script_4.txt')
    with open('example_scripts/example_precond_script_4.json', 'r') as f:
        precond = json.load(f)

    id_mapping = {}
    id_mapping, first_room, room_mapping = helper.add_missing_object_from_script(script, precond, graph_dict, id_mapping)
    print(id_mapping)

    # add random objects
    graph = EnvironmentGraph(graph_dict)

    name_equivalence = utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    state = executor.execute(script)
    if state is None:
        print('Script is not executable, since {}'.format(executor.info.get_error_string()))
    else:
        print('Script is executable')
    

if __name__ == '__main__':
    example_1()
    example_2()
    example_3()
    example_4()
    example_5()
