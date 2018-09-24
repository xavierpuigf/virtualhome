import json
import re


def transform_name_equivalence():
    line_matcher = re.compile(r'([\w_\s]+)\s*->(.*)')
    result = {}

    with open('unity_resources/objects2Unity.txt') as f:
        for line in f:
            line = line.strip().lower()
            line_match = line_matcher.match(line)
            if line_match:
                key = line_match.group(1).strip()
                equiv = []
                values = line_match.group(2)
                for value in values.split(','):
                    value = value.strip()
                    if len(value) > 0 and not value.startswith('!') and value != key:
                        equiv.append(value)

                if len(equiv) > 0:
                    result[key] = equiv

    with open('resources/class_name_equivalence.json', 'w') as f:
        f.write(json.dumps(result))


def transform_object_placing():
    begin_matcher = re.compile(r'BEGIN<([\w_\s]+)>')
    end_matcher = re.compile(r'END<([\w_\s]+)>')
    value_matcher = re.compile(r'([\w_\s]+)[\s]*\[([\w_\s]+)\]')

    result = {}

    with open('unity_resources/placingobjects.txt') as f:
        key = None
        value = None
        for line in f:
            m = begin_matcher.match(line)
            if m:
                key = m.group(1).lower().strip()
            elif end_matcher.match(line):
                key = None
            elif key is not None:
                value = line.lower().strip()
                room = None
                vm = value_matcher.match(value)
                if vm:
                    value = vm.group(1).strip()
                    room = vm.group(2).strip()
                    if len(room) == 0:
                        room = None
                if len(value) > 0:
                    placings = result.setdefault(key, [])
                    placings.append({'destination': value, 'relation': 'ON', 'room': room})

    with open('resources/object_placing.json', 'w') as f:
        f.write(json.dumps(result))


def transform_properties_data():
    result = {}
    with open('unity_resources/properties_data.json') as f:
        u_dict = json.load(f)
    objects = [o.lower().replace(' ', '') for o in u_dict['objects']]
    properties = [p.upper() for p in u_dict['properties']]
    property_matrix = u_dict['property_matrix']
    for i, o in enumerate(objects):
        for j, p in enumerate(properties):
            if property_matrix[i][j] == 1:
                result.setdefault(o, []).append(p)
    with open('resources/properties_data.json', 'w') as f:
        f.write(json.dumps(result))



if __name__ == '__main__':
    # transform_name_equivalence()
    # transform_object_placing()
    transform_properties_data()
