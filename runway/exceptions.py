class RunwayError(Exception):
    def __init__(self):
        super(RunwayError, self).__init__()
        self.message = 'An unknown error occurred.'
        self.code = 500

    def to_response(self):
        return {'error': self.message}


class MissingInputException(RunwayError):
    def __init__(self, name):
        super(MissingInputException, self).__init__()
        self.message = 'Missing input: %s.' % name
        self.code = 400


class InferenceError(RunwayError):
    def __init__(self, message):
        super(InferenceError, self).__init__()
        self.message = 'Inference error: %s' % message
        self.code = 500


class UnknownCommandError(RunwayError):
    def __init__(self, name):
        super(UnknownCommandError, self).__init__()
        self.message = 'Unknown command: %s.' % name
        self.code = 404
