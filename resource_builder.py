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


if __name__ == '__main__':
    transform_name_equivalence()
