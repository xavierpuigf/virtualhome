import time
import uuid


class Error(Exception):
    def __init__(self, message, *args):
        self.message = message.format(*args)

    def __str__(self):
        return self.message


class TimeMeasurement(object):

    _total_time = {}
    _measurement_time = {}

    @classmethod
    def reset_all(cls):
        cls._measurement_time.clear()
        cls._total_time.clear()

    @classmethod
    def start(cls, name):
        key = uuid.uuid4()
        cls._measurement_time[key] = (name, time.time())
        return key

    @classmethod
    def stop(cls, key):
        name, t = cls._measurement_time.get(key, (None, 0))
        if name is not None:
            tt, tn = cls._total_time.get(name, (0, 0))
            cls._total_time[name] = (tt + time.time() - t, tn + 1)

    @classmethod
    def measure_function(cls, name, f):
        tm = cls.start(name)
        result = f()
        TimeMeasurement.stop(tm)
        return result

    @classmethod
    def result_string(cls):
        result = ''
        for key, tn in sorted(cls._total_time.items()):
            result += '{0}: {1}s ({2})\n'.format(key, tn[0], tn[1])
        return result

