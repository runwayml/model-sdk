import os
import sys
import logging
import datetime
import traceback
import json
from flask import Flask, request
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from .exceptions import RunwayError, MissingInputError, MissingOptionError, \
    InferenceError, UnknownCommandError, SetupError
from .data_types import *
from .utils import gzipped, serialize_command, cast_to_obj

class RunwayModel(object):
    def __init__(self):
        self.options = []
        self.setup_fn = None
        self.commands = {}
        self.command_fns = {}
        self.model = None
        self.running_status = 'STARTING'
        self.app = Flask(__name__)
        CORS(self.app)
        self.define_routes()

    def define_routes(self):
        @self.app.route('/')
        def manifest():
            return json.dumps(dict(
                options=[opt.to_dict() for opt in self.options],
                commands=[serialize_command(cmd) for cmd in self.commands.values()]
            ))

        @self.app.route('/healthcheck')
        def healthcheck_route():
            return self.running_status

        @self.app.route('/setup', methods=['POST'])
        def setup_route():
            opts = request.json
            try:
                self.setup_model(opts)
                return json.dumps(dict(success=True))
            except RunwayError as err:
                return json.dumps(err.to_response()), err.code

        @self.app.route('/setup', methods=['GET'])
        def setup_options_route():
            return json.dumps(self.options)

        @self.app.route('/<command_name>', methods=['POST'])
        def command_route(command_name):
            try:
                try:
                    command_fn = self.command_fns[command_name]
                except KeyError:
                    raise UnknownCommandError(command_name)
                inputs = self.commands[command_name]['inputs']
                outputs = self.commands[command_name]['outputs']
                input_dict = request.json
                deserialized_inputs = {}
                for inp in inputs:
                    name = inp.name
                    if name not in input_dict:
                        raise MissingInputError(name)
                    deserialized_inputs[name] = inp.deserialize(input_dict[name])
                try:
                    results = command_fn(self.model, deserialized_inputs)
                    if type(results) != dict:
                        name = outputs[0].name
                        value = results
                        results = {}
                        results[name] = value
                except Exception as err:
                    raise InferenceError(repr(err))

                serialized_outputs = {}
                for out in outputs:
                    name = out.to_dict()['name']
                    serialized_outputs[name] = out.serialize(results[name])
                return json.dumps(serialized_outputs).encode('utf8')

            except RunwayError as err:
                return json.dumps(err.to_response()), err.code

        @self.app.route('/<command_name>', methods=['GET'])
        def usage_route(command_name):
            try:
                try:
                    command = self.commands[command_name]
                except KeyError:
                    raise UnknownCommandError(command_name)
                return json.dumps(serialize_command(command))
            except RunwayError as err:
                return json.dumps(err.to_response())

    def setup(self, decorated_fn=None, options=None):
        if decorated_fn:
            self.options = []
            self.setup_fn = decorated_fn
        else:
            def decorator(fn):
                self.options = []
                for name, opt in options.items():
                    opt = cast_to_obj(opt)
                    opt.name = name
                    self.options.append(opt)
                self.setup_fn = fn
                return fn
            return decorator

    def command(self, name, inputs={}, outputs={}):
        if len(inputs.values()) == 0 or len(outputs.values()) == 0:
            raise Exception('You need to provide at least one input and output for the command')

        inputs_as_list = []
        for input_name, inp in inputs.items():
            inp_obj = cast_to_obj(inp)
            inp_obj.name = input_name
            inputs_as_list.append(inp_obj)

        outputs_as_list = []
        for output_name, out in outputs.items():
            out_obj = cast_to_obj(out)
            out_obj.name = output_name
            outputs_as_list.append(out_obj)

        command_info = dict(
            name=name,
            inputs=inputs_as_list,
            outputs=outputs_as_list
        )

        self.commands[name] = command_info

        def decorator(fn):
            self.command_fns[name] = fn
            return fn

        return decorator

    def setup_model(self, opts):
        self.running_status = 'STARTING'
        if self.setup_fn and self.options:
            deserialized_opts = {}
            for opt in self.options:
                name = opt.name
                opt = cast_to_obj(opt)
                opt.name = name
                if name in opts:
                    deserialized_opts[name] = opt.deserialize(opts[name])
                elif getattr(opt, 'default', None) is not None:
                    deserialized_opts[name] = opt.default
                else:
                    raise MissingOptionError(name)
            self.model = self.setup_fn(deserialized_opts)
        elif self.setup_fn:
            self.model = self.setup_fn()
        self.running_status = 'RUNNING'

    def run(self, host='0.0.0.0', port=8000, model_options={}, debug=False, meta=False):

        env_host          = os.getenv('RW_HOST')
        env_port          = os.getenv('RW_PORT')
        env_meta          = os.getenv('RW_META')
        env_debug         = os.getenv('RW_DEBUG')
        env_model_options = os.getenv('RW_MODEL_OPTIONS')

        if env_host is not None:  host = env_host
        if env_port is not None:  port = int(env_port)
        if env_meta is not None:  meta = bool(int(env_meta))
        if env_debug is not None: debug = bool(int(env_debug))
        if env_model_options is not None:
            model_options = json.loads(env_model_options)

        if meta:
            print(json.dumps(dict(
                options=[opt.to_dict() for opt in self.options],
                commands=[serialize_command(cmd) for cmd in self.commands.values()]
            )))
            return
        print('Setting up model...')
        try:
            self.setup_model(model_options)
        except RunwayError as err:
            resp = err.to_response()
            print(resp['error'])
            sys.exit(1)
        print('Starting model server at http://{0}:{1}...'.format(host, port))
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            self.app.debug = True
            self.app.run(host=host, port=port, debug=True, threaded=True)
        else:
            http_server = WSGIServer((host, port), self.app)
            try:
                http_server.serve_forever()
            except KeyboardInterrupt:
                print('Stopping server...')
