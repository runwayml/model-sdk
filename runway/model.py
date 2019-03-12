import os
import sys
import inspect
import logging
import datetime
import traceback
from argparse import ArgumentParser
import json
from flask import Flask, request
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from .exceptions import RunwayError, MissingInputException, MissingOptionException, \
                        InferenceError, UnknownCommandError, SetupError
from .data_types import *
from .utils import gzipped, serialize_command


class RunwayModel(object):
    def __init__(self):
        self.options = {}
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
                    inputs = self.commands[command_name]['inputs']
                    outputs = self.commands[command_name]['outputs']
                except KeyError:
                    raise UnknownCommandError(command_name)
                input_dict = request.json
                deserialized_inputs = []
                for inp in inputs:
                    name = inp.name
                    if getattr(inp, 'default', None) is None and name not in input_dict:
                        raise MissingInputException(name)
                    deserialized_inputs.append(inp.deserialize(input_dict[name]) or getattr(inp, 'default', None))
                try:
                    results = command_fn(self.model, *deserialized_inputs)
                    results = (results,) if type(results) != tuple else results
                except Exception as err:
                    raise InferenceError(repr(err))
                serialized_outputs = {}
                for index, out in enumerate(outputs):
                    name = out.to_dict()['name']
                    serialized_outputs[name] = out.serialize(results[index])
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
                    opt.name = name
                    self.options.append(opt)
                self.setup_fn = fn
                return fn
            return decorator

    def command(self, name, inputs=[], outputs=[]):
        if len(inputs) == 0 or len(outputs) == 0:
            raise Exception('You need to provide at least one input and output for the command')
        def cast_to_obj(cls_or_obj):
            if inspect.isclass(cls_or_obj): return cls_or_obj()
            return cls_or_obj
        command_info = dict(
            name=name,
            inputs=[cast_to_obj(inp) for inp in inputs],
            outputs=[cast_to_obj(out) for out in outputs]
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
                if name in opts:
                    deserialized_opts[name] = opt.deserialize(opts[name])
                elif getattr(opt, 'default', None) is not None:
                    deserialized_opts[name] = opt.default
                else:
                    raise MissingOptionException(name)
            self.model = self.setup_fn(deserialized_opts)
        elif self.setup_fn:
            self.model = self.setup_fn()
        self.running_status = 'RUNNING'
            
    def run(self):
        parser = ArgumentParser()
        parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for the model server')
        parser.add_argument('--port', type=int, default=8000, help='Port for the model server')
        parser.add_argument('--rw_model_options', type=str, default=os.getenv(
            'RW_MODEL_OPTIONS', '{}'), help='Pass options to the Runway model as a JSON string')
        parser.add_argument('--debug', action='store_true', help='Activate debug mode (live reload)')
        parser.add_argument('--meta', action='store_true', help='Print model manifest')
                            
        args = parser.parse_args()
        host = args.host
        port = args.port
        if args.meta:
            print(json.dumps(dict(
                options=[opt.to_dict() for opt in self.options],
                commands=[serialize_command(cmd) for cmd in self.commands.values()]
            )))
            return
        print('Setting up model...')
        try:
            self.setup_model(json.loads(args.rw_model_options))
        except RunwayError as err:
            resp = err.to_response()
            print(resp['error'])
            sys.exit(1)
        print('Starting model server at http://{0}:{1}...'.format(host, port))
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
            self.app.debug = True
            self.app.run(host=host, port=port, debug=True, threaded=True)
        else:
            http_server = WSGIServer((host, port), self.app)
            try:
                http_server.serve_forever()
            except KeyboardInterrupt:
                print('Stopping server...')
