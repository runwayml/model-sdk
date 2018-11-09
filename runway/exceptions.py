class RunwayError(Exception):
    def __init__(self):
        super(RunwayError, self).__init__()
        self.message = 'An unknown error occurred.'

    def to_response(self):
        return {'error': self.message}


class MissingInputException(RunwayError):
    def __init__(self, name):
        super(MissingInputException, self).__init__()
        self.message = 'Missing input: %s.' % name
