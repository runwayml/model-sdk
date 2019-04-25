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

os.environ['RW_NO_SERVE'] = '1'

# Testing Flask Applications: http://flask.pocoo.org/docs/1.0/testing/
def test_model_setup_and_command():

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

    setup_ran = False
    command_ran = False

    rw = RunwayModel()

    @rw.setup(options={ 'size': category(choices=['big', 'small']) })
    def setup(opts):
        nonlocal setup_ran
        setup_ran = True
        return {}

    inputs = { 'input': text }
    outputs = { 'output': number }
    @rw.command('test_command', inputs=inputs, outputs=outputs)
    def test_command(model, opts):
        nonlocal command_ran
        command_ran = True
        return 100

    rw.run(debug=True)

    client = get_test_client(rw)

    # check the manifest via a GET /
    response = client.get('/')
    manifest = json.loads(response.data)
    assert manifest == expected_manifest

    # check the input/output manifest for GET /test_command
    response = client.get('/test_command')
    command_manifest = json.loads(response.data)
    assert command_manifest == expected_manifest['commands'][0]

    post_data = {
        'input': 'test input'
    }
    response = client.post('/test_command', json=post_data)
    assert json.loads(response.data) == { 'output' : 100 }

    assert command_ran == True
    assert setup_ran == True

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
    rw = RunwayModel()
    setup_ran = False
    # Any reason @rw.setup called with no arguments requires the decorated
    # function NOT to have arguments? This seems a bit like an idiosyncracy to
    # me. Why not keep the function signature of the wrapped function the
    # same regardless and simply pass an empty dict in the case of no options?
    @rw.setup
    def setup():
        nonlocal setup_ran
        setup_ran = True

    rw.run(debug=True)
    assert setup_ran == True

def test_model_options_passed_as_arguments_to_run():
    rw = RunwayModel()
    setup_ran = False
    @rw.setup(options={'initialization_array': array(item_type=text)})
    def setup(opts):
        nonlocal setup_ran
        assert opts['initialization_array'] == ['one', 'two', 'three']
        setup_ran = True

    rw.run(debug=True, model_options={ 'initialization_array': ['one', 'two', 'three'] })
    assert setup_ran == True

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
            'vector': vector(length=32)
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
        "options": [{
            "name": "initialization_array",
            "type": "array",
            "itemType": {
                "type": "text",
                "name": "text",
                "default": "",
                "minLength": 0
            },
            "minLength": 0
        }],
        "commands": [{
            "name": "command_1",
            "inputs": [{
                "type": "image",
                "name": "image",
                "channels": 3
            }, {
                "type": "vector",
                "name": "vector",
                "length": 32,
                "samplingMean": 0,
                "samplingStd": 1
            }],
            "outputs": [{
                "type": "text",
                "name": "label",
                "default": "",
                "minLength": 0
            }]
        },
        {
            "name": "command_2",
            "inputs": [{
                "type": "any",
                "name": "any"
                }, {
                "type": "file",
                "name": "file"
            }],
            "outputs": [{
                "type": "number",
                "name": "number",
                "default": 0,
                "min": 10,
                "max": 100,
                "step": 1
            }]
        }]
    }

    meta_before = os.environ.get('RW_META')
    os.environ['RW_META'] = '1'

    rw.run(debug=True, model_options={ 'initialization_array': ['one', 'two', 'three'] })
    std = capsys.readouterr()
    assert json.loads(std.out) == expected_manifest
    assert std.err == ''

    if meta_before is not None: os.environ['RW_META'] = meta_before

