import sys
import traceback

class RunwayError(Exception):
    """A base error class that defines an HTTP error code, an error message,
    and can be formatted as an object to be returned as JSON in an HTTP request.

    :ivar message: An error message, set to "An unknown error occurred."
    :type message: string
    :ivar code: An HTTP error code, set to 500
    :type code: number
    """
    def __init__(self):
        super(RunwayError, self).__init__()
        self.message = 'An unknown error occurred.'
        self.code = 500

    def get_traceback(self):
        """Return a list of lines containing the traceback of the exception \
        currently being handled.

        :return A list of lines of the exception traceback
        :rtype list
        """
        _, _, tb = sys.exc_info()
        traceback_lines = traceback.format_tb(tb)
        return [l.strip() for l in traceback_lines]

    def print_exception(self):
        """Print the exception message and traceback to stderr."""
        sys.stderr.write('\033[91m\n')
        sys.stderr.write(self.message + '\n')
        for line in self.get_traceback():
            sys.stderr.write(line + '\n')
        sys.stderr.write('\033[0m' + '\n')

    def to_response(self):
        """Get information about the error formatted as a dictionary.

        :return: An object containing "error" and "traceback" keys.
        :rtype: dict
        """
        return {'error': self.message, 'traceback': self.get_traceback()}

class MissingOptionError(RunwayError):
    """Thrown by the ``@runway.setup()`` decorator when a required option value
    has not been provided by the user.

    :ivar message: An error message, set to "Missing option:
        {NAME_OF_MISSING_OPTION}"
    :type message: string
    :ivar code: An HTTP error code, set to 400
    :type code: number
    """
    def __init__(self, name):
        super(MissingOptionError, self).__init__()
        self.message = 'Missing option: %s.' % name
        self.code = 400


class MissingInputError(RunwayError):
    """Thrown by the ``@runway.command()`` decorator when a required input value
    has not been provided by the user.

    :ivar message: An error message, set to "Missing input:
        {NAME_OF_MISSING_OPTION}"
    :type message: string
    :ivar code: An HTTP error code, set to 400
    :type code: number
    """
    def __init__(self, name):
        super(MissingInputError, self).__init__()
        self.message = 'Missing input: %s.' % name
        self.code = 400


class InvalidArgumentError(RunwayError):
    """An error indicating that an argument is invalid.
    May be raised by ``@runway.setup()`` or ``@runway.command()`` decorated
    functions if they receive a bad input value.

    :ivar message: An error message, set to "Invalid argument:
        {NAME_OF_MISSING_OPTION}"
    :type message: string
    :ivar code: An HTTP error code, set to 400
    :type code: number
    """
    def __init__(self, name):
        super(InvalidArgumentError, self).__init__()
        self.message = 'Invalid argument: %s.' % name
        self.code = 400


class InferenceError(RunwayError):
    """An error thrown if there is an uncaught exception in a function
    decorated by ``@runway.command()``. If this error is thrown, there is an
    exception in your code ;)

    :ivar message: A repr() of original exception
    :type message: string
    :ivar code: An HTTP error code, set to 500
    :type code: number
    """
    def __init__(self, message):
        super(InferenceError, self).__init__()
        self.message = 'Error during inference: %s.' % message
        self.code = 500


class UnknownCommandError(RunwayError):
    """
    An error thrown if an HTTP request is made to an endpoint that doesn't
    exist. E.g. ``http://localhost:8000/nothing_here``.

    :ivar message: An error message, set to "Unknown command:
        {COMMAND_NAME}"
    :type message: string
    :ivar code: An HTTP error code, set to 404
    :type code: number
    """
    def __init__(self, name):
        super(UnknownCommandError, self).__init__()
        self.message = 'Unknown command: %s.' % name
        self.code = 404


class SetupError(RunwayError):
    """An error thrown if there is an uncaught exception in a function
    decorated by ``@runway.setup()``. If this error is thrown, there is an
    exception in your code ;)

    :ivar message: A repr() of original exception
    :type message: string
    :ivar code: An HTTP error code, set to 500
    :type code: number
    """
    def __init__(self, message):
        super(SetupError, self).__init__()
        self.message = 'Error during setup: %s.' % message
        self.code = 500


class MissingArgumentError(RunwayError):
    """An error thrown when a required function argument is not provided.

    :ivar message: An error message, set to "Missing argument:
    {ARGUMENT_NAME}"
    :type message: string
    :ivar code: An HTTP error code, set to 500
    :type code: number
    """
    def __init__(self, arg):
        super(MissingArgumentError, self).__init__()
        self.message = 'Missing argument: %s.' % arg
        self.code = 500
