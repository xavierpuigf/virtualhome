import script
import json

class TestClass(object):
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __str__(self):
        return '({0}, {1})'.format(self.first, self.second)

def run_test(line, **kwargs):
    script.parse_script_line(line)
    print(kwargs['object'])


if __name__ == '__main__':
    run_test('[PUT] <bottle> (1) <table> (1)', object='a', subject='b')
    s = '{"second": "one", "first": 1}'
    d = json.loads(s, object_hook=lambda d: TestClass(**d))
    print(d)
