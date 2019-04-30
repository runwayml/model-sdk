# Ensure that the local version of the runway module is used, not a pip
# installed version
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')

import os
import json
import pytest
from runway.model import RunwayModel
from runway.data_types import category, text, number, array, image, vector, file, any as any_type
from runway.exceptions import *
from utils import get_test_client
from deepdiff import DeepDiff
from flask import abort

os.environ['RW_NO_SERVE'] = '1'

# Testing Flask Applications: http://flask.pocoo.org/docs/1.0/testing/
def test_model_setup_and_command():

    # use a dict to share state across function scopes. This makes up for the
    # fact that Python 2.x doesn't have support for the 'nonlocal' keyword.
    closure = dict(setup_ran = False, command_ran = False)

    expected_manifest = {
        'options': [{
            'type': 'category',
            'name': 'size',
            'oneOf': ['big', 'small'],
            'default': 'big'
        }],
        'commands': [{
            'name': 'test_command',
            'inputs': [{
                'type': 'text',
                'name': 'input',
                'default': '',
                'minLength': 0
            }],
            'outputs': [{
                'type': 'number',
                'name': 'output',
                'default': 0,
                'min': 0,
                'max': 1,
                'step': 1
            }]
        }]
    }

    rw = RunwayModel()

    @rw.setup(options={ 'size': category(choices=['big', 'small']) })
    def setup(opts):
        closure['setup_ran'] = True
        return {}

    inputs = { 'input': text }
    outputs = { 'output': number }
    @rw.command('test_command', inputs=inputs, outputs=outputs)
    def test_command(model, opts):
        closure['command_ran'] = True
        return 100

    rw.run(debug=True)

    client = get_test_client(rw)

    # check the manifest via a GET /
    response = client.get('/')
    assert response.is_json

    manifest = json.loads(response.data)
    assert manifest == expected_manifest

    # check the input/output manifest for GET /test_command
    response = client.get('/test_command')
    assert response.is_json

    command_manifest = json.loads(response.data)
    assert command_manifest == expected_manifest['commands'][0]

    post_data = {
        'input': 'test input'
    }
    response = client.post('/test_command', json=post_data)
    assert response.is_json
    assert json.loads(response.data) == { 'output' : 100 }

    assert closure['command_ran'] == True
    assert closure['setup_ran'] == True

def test_model_status():
    rw = RunwayModel()
    assert rw.running_status == 'STARTING'
    rw.run(debug=True)
    assert rw.running_status == 'RUNNING'

def test_model_healthcheck():
    rw = RunwayModel()
    rw.run(debug=True)
    client = get_test_client(rw)
    response = client.get('/healthcheck')
    assert response.data == b'RUNNING'

def test_model_setup_no_arguments():

    # use a dict to share state across function scopes. This makes up for the
    # fact that Python 2.x doesn't have support for the 'nonlocal' keyword.
    closure = dict(setup_ran = False)

    rw = RunwayModel()

    # Any reason @rw.setup called with no arguments requires the decorated
    # function NOT to have arguments? This seems a bit like an idiosyncracy to
    # me. Why not keep the function signature of the wrapped function the
    # same regardless and simply pass an empty dict in the case of no options?
    @rw.setup
    def setup():
        closure['setup_ran'] = True

    rw.run(debug=True)
    assert closure['setup_ran'] == True

def test_model_options_passed_as_arguments_to_run():

    # use a dict to share state across function scopes. This makes up for the
    # fact that Python 2.x doesn't have support for the 'nonlocal' keyword.
    closure = dict(setup_ran = False)

    rw = RunwayModel()
    @rw.setup(options={'initialization_array': array(item_type=text)})
    def setup(opts):
        assert opts['initialization_array'] == ['one', 'two', 'three']
        closure['setup_ran'] = True

    rw.run(debug=True, model_options={ 'initialization_array': ['one', 'two', 'three'] })
    assert closure['setup_ran'] == True

def test_model_options_missing():

    rw = RunwayModel()
    @rw.setup(options={'initialization_array': array(item_type=text)})
    def setup(opts):
        pass

    # this will print to stderr still, but the test should pass
    with pytest.raises(SystemExit):
        with pytest.raises(MissingOptionError):
            rw.run(debug=True)

def test_meta(capsys):

    rw = RunwayModel()

    @rw.setup(options={'initialization_array': array(item_type=text)})
    def setup(opts):
        pass

    kwargs_1 = {
        'inputs': {
            'image': image,
            'vector': vector(length=5)
        },
        'outputs': {
            'label': text
        }
    }
    @rw.command('command_1', **kwargs_1)
    def command_1(opts):
        pass

    kwargs_2 = {
        'inputs': {
            'any': any_type,
            'file': file
        },
        'outputs': {
            'number': number(min=10, max=100)
        }
    }

    @rw.command('command_2', **kwargs_2)
    def command_2(opts):
        pass

    expected_manifest = {
        'options': [
            {
                'minLength': 0,
                'type': 'array',
                'name': 'initialization_array',
                'itemType': {
                    'default': '',
                    'minLength': 0,
                    'type': 'text',
                    'name': 'text'
                }
            }
        ],
        'commands': [
            {
                'name': 'command_2',
                'inputs': [
                    {
                        'type': 'any',
                        'name': 'any',
                    },
                    {
                        'type': 'file',
                        'name': 'file',
                    },
                ],
                'outputs': [
                    {
                        'name': 'number',
                        'min': 10,
                        'default': 0,
                        'max': 100,
                        'step': 1,
                        'type': 'number',
                    },
                ]
            },
            {
                'name': 'command_1',
                'inputs': [
                    {
                        'channels': 3,
                        'type': 'image',
                        'name': 'image',
                    },
                    {
                        'samplingMean': 0,
                        'length': 5,
                        'type': 'vector',
                        'name': 'vector',
                        'samplingStd': 1,
                        'default': [0, 0, 0, 0, 0]
                    },
                ],
                'outputs': [
                    {
                        'default': '',
                        'minLength': 0,
                        'type': 'text',
                        'name': 'label'
                    }
                ]
            }
        ]
    }

    # RW_META should not be set during testing
    os.environ['RW_META'] = '1'

    rw.run(debug=True, model_options={ 'initialization_array': ['one', 'two', 'three'] })
    std = capsys.readouterr()
    manifest = json.loads(std.out.strip('\n'))

    # DeepDiff is required here because Python2 handles stdin encoding strangely
    # and because dict order is not guaranteed in Python2. I ran up a tree
    # trying to get this comparison working without relying on a lib, but
    # ultimately it was just wasting my time.
    diff = DeepDiff(manifest, expected_manifest, ignore_order=True)
    assert len(diff.keys()) == 0
    assert std.err == ''

    os.environ['RW_META'] = '0'

def test_post_setup_json_no_mime_type():

    rw = RunwayModel()

    @rw.setup(options={'input': text})
    def setup(opts):
        pass

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.post('/setup', data='{"input": "test input"}')
    assert response.is_json
    assert json.loads(response.data) == { 'success': True }

def test_post_setup_invalid_json_no_mime_type():

    rw = RunwayModel()

    @rw.setup(options={'input': text})
    def setup(opts):
        pass

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.post('/setup', data='{"input": test input"}')

    assert response.is_json
    assert response.status_code == 400

    expect = { 'error': 'The body of all POST requests must contain JSON' }
    assert json.loads(response.data) == expect


def test_post_setup_json_mime_type():

    rw = RunwayModel()

    @rw.setup(options={'input': text})
    def setup(opts):
        pass

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.post('/setup', json={ 'input': 'test input' })
    assert response.is_json
    assert json.loads(response.data) == { 'success': True }

def test_post_setup_form_encoding():

    rw = RunwayModel()

    @rw.setup(options={'input': text})
    def setup(opts):
        pass

    rw.run(debug=True)

    client = get_test_client(rw)

    content_type='application/x-www-form-urlencoded'
    response = client.post('/setup', data='input=test', content_type=content_type)

    assert response.is_json
    assert response.status_code == 400

    expect = { 'error': 'The body of all POST requests must contain JSON' }
    assert json.loads(response.data) == expect

def test_post_command_json_no_mime_type():

    rw = RunwayModel()

    @rw.command('times_two', inputs={ 'input': number }, outputs={ 'output': number })
    def times_two(model, args):
        return args['input'] * 2

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.post('/times_two', data='{ "input": 5 }')
    assert response.is_json
    assert json.loads(response.data) == { 'output': 10 }

def test_post_command_json_mime_type():

    rw = RunwayModel()

    @rw.command('times_two', inputs={ 'input': number }, outputs={ 'output': number })
    def times_two(model, args):
        return args['input'] * 2

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.post('/times_two', json={ 'input': 5 })
    assert response.is_json
    assert json.loads(response.data) == { 'output': 10 }

def test_post_command_form_encoding():

    rw = RunwayModel()

    @rw.command('times_two', inputs={ 'input': number }, outputs={ 'output': number })
    def times_two(model, args):
        return args['input'] * 2

    rw.run(debug=True)

    client = get_test_client(rw)

    content_type='application/x-www-form-urlencoded'
    response = client.post('/times_two', data='input=5', content_type=content_type)
    assert response.is_json
    assert response.status_code == 400

    expect = { 'error': 'The body of all POST requests must contain JSON' }
    assert json.loads(response.data) == expect

def test_405_method_not_allowed():

    rw = RunwayModel()

    @rw.setup(options={'input': text})
    def setup(opts):
        pass

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.put('/setup', json= { 'input': 'test input'})

    assert response.is_json
    assert response.status_code == 405
    assert response.json == { 'error': 'Method not allowed.' }

def test_404_not_found():

    rw = RunwayModel()

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.get('/asfd')

    assert response.is_json
    assert response.status_code == 404

def test_401_unauthorized():

    rw = RunwayModel()

    @rw.app.route('/test/unauthorized')
    def unauthorized():
        abort(401)

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.get('/test/unauthorized')

    assert response.is_json
    assert response.status_code == 401

    expect = { 'error': 'Unauthorized (well... really unauthenticated but hey I didn\'t write the spec).' }
    assert response.json == expect

def test_403_forbidden():

    rw = RunwayModel()

    @rw.app.route('/test/forbidden')
    def unauthorized():
        abort(403)

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.get('/test/forbidden')

    assert response.is_json
    assert response.status_code == 403

    expect = { 'error': 'Forbidden.' }
    assert response.json == expect

def test_500_internal_server_error():

    rw = RunwayModel()

    @rw.app.route('/test/internal_server_error')
    def unauthorized():
        abort(500)

    rw.run(debug=True)

    client = get_test_client(rw)
    response = client.get('/test/internal_server_error')

    assert response.is_json
    assert response.status_code == 500

    expect = { 'error': 'Internal server error.' }
    assert response.json == expect

def test_setup_error_setup_no_args():

    rw = RunwayModel()

    @rw.setup
    def setup():
        raise Exception('test exception, thrown from inside a wrapped setup() function')

    with pytest.raises(SystemExit):
        with pytest.raises(SetupError):
            rw.run(debug=True)


def test_setup_error_setup_with_args():

    rw = RunwayModel()

    @rw.setup(options={'input': text})
    def setup(opts):
        raise Exception('test exception, thrown from inside a wrapped setup() function')

    with pytest.raises(SystemExit):
        with pytest.raises(SetupError):
            rw.run(debug=True)

def test_inference_error():

    rw = RunwayModel()
    client = get_test_client(rw)

    @rw.command('test_command', inputs={ 'input': number }, outputs = { 'output': text })
    def test_command(model, inputs):
        raise Exception('test exception, thrown from inside a wrapped command() function')

    rw.run(debug=True)

    response = client.post('test_command', json={ 'input': 5 })
    assert response.is_json
    assert 'InferenceError' in str(response.data)
