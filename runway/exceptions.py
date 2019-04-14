import sys
import traceback

class RunwayError(Exception):
    def __init__(self):
        super(RunwayError, self).__init__()
        self.message = 'An unknown error occurred.'
        self.code = 500

    def get_traceback(self):
        _, _, tb = sys.exc_info()
        traceback_lines = traceback.format_tb(tb)
        return [l.strip() for l in traceback_lines]

    def print(self):
        print('\033[91m')
        print(self.message)
        for line in self.get_traceback():
            print(line)
        print('\033[0m')

    def to_response(self):
        return {'error': self.message, 'traceback': self.get_traceback()}


class MissingOptionError(RunwayError):
    def __init__(self, name):
        super(MissingOptionError, self).__init__()
        self.message = 'Missing option: %s.' % name
        self.code = 400


class MissingInputError(RunwayError):
    def __init__(self, name):
        super(MissingInputError, self).__init__()
        self.message = 'Missing input: %s.' % name
        self.code = 400


class InvalidInputError(RunwayError):
    def __init__(self, name):
        super(InvalidInputError, self).__init__()
        self.message = 'Invalid input: %s.' % name
        self.code = 400


class InferenceError(RunwayError):
    def __init__(self, message):
        super(InferenceError, self).__init__()
        self.message = 'Error during inference: %s.' % message
        self.code = 500


class UnknownCommandError(RunwayError):
    def __init__(self, name):
        super(UnknownCommandError, self).__init__()
        self.message = 'Unknown command: %s.' % name
        self.code = 404


class SetupError(RunwayError):
    def __init__(self, message):
        super(SetupError, self).__init__()
        self.message = 'Error during setup: %s' % message
        self.code = 500


class MissingArgumentError(RunwayError):
    def __init__(self, arg):
        super(MissingArgumentError, self).__init__()
        self.message = 'Missing argument: %s' % arg
        self.code = 500
