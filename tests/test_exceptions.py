# Ensure that the local version of the runway module is used, not a pip
# installed version
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')

import pytest
from runway.exceptions import *
from runway import exceptions
import runway

def get_exceptions():
    error_names = [name for name in dir(exceptions) if name.endswith('Error')]
    return {name: getattr(exceptions, name) for name in error_names}

def check_to_response_method(err):
    response = err.to_response()
    assert type(response) == dict
    assert 'error' in response
    assert 'traceback' in response
    assert len(response['error']) > 0
    assert len(response['traceback']) > 0

def check_code_and_error(error_class,
                         expected_code,
                         expected_message,
                         inpt=None):
    try:
        if inpt is not None:
            raise error_class(inpt)
        else:
            raise error_class()
    except RunwayError as err:
        assert err.code == expected_code
        assert err.message == expected_message

# Going for the longest function name award here. The whole signature is 80 char
def test_all_runway_errors_have_code_and_message_props_and_to_response_method():
    for name, error in get_exceptions().items():
        try:
            if name == 'RunwayError':
                raise error()
            else:
                raise error('test error message.')
        except error as err:
            assert type(err.message) == str
            assert type(err.code) == int
            assert err.code >= 400
            check_to_response_method(err)

def test_runway_error():
    check_code_and_error(RunwayError, 500, 'An unknown error occurred.')

def test_missing_option_error():
    expect = 'Missing option: test_option.'
    check_code_and_error(MissingOptionError, 400, expect, inpt='test_option')

def test_missing_input_error():
    expect = 'Missing input: test_option.'
    check_code_and_error(MissingInputError, 400, expect, inpt='test_option')

def test_invalid_input_error():
    expect = 'Invalid input: test_option.'
    check_code_and_error(InvalidInputError, 400, expect, inpt='test_option')

def test_inference_error():
    expect = 'Error during inference: test_option.'
    check_code_and_error(InferenceError, 500, expect, inpt='test_option')

def test_unknown_command_error():
    expect = 'Unknown command: test_option.'
    check_code_and_error(UnknownCommandError, 404, expect, inpt='test_option')

def test_setup_error():
    expect = 'Error during setup: test_option.'
    check_code_and_error(SetupError, 500, expect, inpt='test_option')

def test_missing_argument_error():
    expect = 'Missing argument: test_option.'
    check_code_and_error(MissingArgumentError, 500, expect, inpt='test_option')
