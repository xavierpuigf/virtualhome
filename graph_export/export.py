from graph_export.scriptcheck import UnityCommunication
import json
import sys


def export_graph(file_name):
    comm = UnityCommunication()
    success, graph = comm.environment_graph()
    with open('../example_graphs/' + file_name, 'w') as file:
        json.dump(graph, file)
        print('Exported "{}"'.format(file_name))


if __name__ == '__main__':
    file_name_pattern = 'TestScene{}_graph.json'
    while True:
        scene_index = input('Enter scene index (integer): ')
        if not scene_index.isnumeric():
            break
        export_graph(file_name_pattern.format(scene_index))
