import json
from environment import EnvironmentGraph


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)


def load_name_equivalence(file_name='resources/class_name_equivalence.json'):
    with open(file_name) as f:
        return json.load(f)

