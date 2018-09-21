import utils
from execution import Relation
from scripts import read_script
from execution import ScriptExecutor


def print_node_names(n_list):
    if len(n_list) > 0:
        print([n.class_name for n in n_list])


if __name__ == '__main__':
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
