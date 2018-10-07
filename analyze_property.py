# check which objects have the specified properties

import json
from termcolor import colored


path = 'resources/properties_data.json'

property = json.load(open(path, 'r'))
objects = list(property.keys())

print("Number of objects: {}".format(len(objects)))
property_list = []
for v in property.values():
    property_list.extend(v)

property_list = list(set(property_list))

def print_property():
    print("Number of properties: {}".format(len(property_list)))
    print("-"*30)
    print(property_list)


def compare_two_lists(complete_list, sublist):
    complete_list = set(complete_list)
    sublist = set(sublist)

    overlap = complete_list & sublist
    return len(overlap) == len(sublist)

# specify the property
while(True):
    print_property()

    print("-"*30)
    print("Specify the properties:")
    specified_property = input()
    specified_property = specified_property.upper()
    specified_property = specified_property.split(', ')
    print("Specified properties:", specified_property)

    for obj in objects:
        if compare_two_lists(property[obj], specified_property):
            print(colored(obj, 'cyan'))