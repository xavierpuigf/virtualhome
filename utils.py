import json
from environment import EnvironmentGraph, Property


def load_graph(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return EnvironmentGraph(data)


def load_name_equivalence(file_name='resources/class_name_equivalence.json'):
    with open(file_name) as f:
        return json.load(f)


def load_object_placing(file_name='resources/object_placing.json'):
    with open(file_name) as f:
        return json.load(f)


def load_properties_data(file_name='resources/properties_data.json'):
    with open(file_name) as f:
        pd_dict = json.load(f)
        return {key: [Property[p] for p in props] for (key, props) in pd_dict.items()}
