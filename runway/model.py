import os
import sys
import logging
import datetime
import traceback
from argparse import ArgumentParser
import json
from flask import Flask, request
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from .exceptions import RunwayError, MissingInputException, MissingOptionException, InferenceError, UnknownCommandError, SetupError
from .io import serialize, deserialize
from .utils import gzipped


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
                options=self.options,
                commands=self.commands
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
                for input_name, input_type in inputs.items():
                    if input_name not in input_dict:
                        raise MissingInputException(input_name)
                    input_dict[input_name] = deserialize(
                        input_dict[input_name], input_type)
                try:
                    output_dict = command_fn(self.model, input_dict)
                except Exception as err:
                    raise InferenceError(repr(err))
                for output_name, output_type in outputs.items():
                    output_dict[output_name] = serialize(
                        output_dict[output_name], output_type)
                return json.dumps(output_dict).encode('utf8')
            except RunwayError as err:
                return json.dumps(err.to_response()), err.code

        @self.app.route('/<command_name>', methods=['GET'])
        def usage_route(command_name):
            try:
                try:
                    command = self.commands[command_name]
                except KeyError:
                    raise UnknownCommandError(command_name)
                return json.dumps(command)
            except RunwayError as err:
                return json.dumps(err.to_response())

    def setup(self, decorated_fn=None, options=None):
        if decorated_fn:
            self.options = {}
            self.setup_fn = decorated_fn
        else:
            def decorator(fn):
                self.options = options
                self.setup_fn = fn
                return fn
            return decorator

    def command(self, name, inputs=None, outputs=None):
        if inputs is None or outputs is None:
            raise Exception('You need to provide inputs and outputs for the command')
        command_info = dict(inputs=inputs, outputs=outputs)
        self.commands[name] = command_info
        def decorator(fn):
            self.command_fns[name] = fn
            return fn
        return decorator

    def setup_model(self, opts):
        try:
            self.running_status = 'STARTING'
            if self.setup_fn and self.options:
                for name, value in opts.items():
                    opts[name] = deserialize(value, self.options[name])
                self.model = self.setup_fn(opts)
            elif self.setup_fn:
                self.model = self.setup_fn()
            self.running_status = 'RUNNING'
        except Exception as err:
            self.running_status = 'FAILED'
            raise SetupError(repr(err))

    def run(self):
        parser = ArgumentParser()
        parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for the model server')
        parser.add_argument('--port', type=int, default=9000, help='Port for the model server')
        parser.add_argument('--rw_model_options', type=str, default=os.getenv(
            'RW_MODEL_OPTIONS', '{}'), help='Pass options to the Runway model as a JSON string')
        parser.add_argument('--debug', action='store_true',
                            help='Activate debug mode (live reload)')
        parser.add_argument('--manifest', action='store_true',
                            help='Print model manifest')
        args = parser.parse_args()
        host = args.host
        port = args.port
        if args.manifest:
            print(json.dumps(dict(options=self.options, commands=self.commands)))
            return
        print('Setting up model...')
        try:
            self.setup_model(json.loads(args.rw_model_options))
        except RunwayError as err:
            resp = err.to_response()
            print(resp['error'])
            print(resp['traceback'])
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
