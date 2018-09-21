from graph_export   .scriptcheck import UnityCommunication
import json
import sys


def export_graph(file_name):
    comm = UnityCommunication()
    success, graph = comm.environment_graph()
    with open('../example_graphs/' + file_name, 'w') as file:
        json.dump(graph, file)


if __name__ == '__main__':
    file_name = 'graph.json'
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    export_graph(file_name)
