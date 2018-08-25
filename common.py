
class Error(Exception):
    def __init__(self, message, *args):
        self.message = message.format(*args)

    def __str__(self):
        return self.message
