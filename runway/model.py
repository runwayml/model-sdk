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
from .exceptions import RunwayError, MissingInputException, MissingOptionException, InferenceError, UnknownCommandError
from .io import serialize, deserialize
from .utils import to_long_spec, gzipped


__version__ = '0.0.37'


class RunwayModel(object):
    def __init__(self):
        self.setup_fn = None
        self.options = None
        self.commands = {}
        self.command_fns = {}
        self.model = None
        self.accessed = None
        self.opts = self.parse_opts()
        self.app = Flask(__name__)
        CORS(self.app)
        self.define_routes()

    def define_routes(self):
        @self.app.route('/healthcheck')
        def healthcheck():
            return 'ok'

        @self.app.route('/')
        def manifest():
            return json.dumps(
                startedAt=self.started,
                lastAccessedAt=self.accessed,
                apiVersion=__version__,
                modelOptions=json.loads(self.opts.rw_model_options),
                commands=self.commands
            )

        @gzipped
        @self.app.route('/<command_name>', methods=['POST'])
        def command(command_name):
            self.started = datetime.datetime.utcnow().isoformat()
            try:
                try:
                    command_fn = self.command_fns[command_name]
                    inputs = self.commands[command_name]['inputs']
                    outputs = self.commands[command_name]['outputs']
                except KeyError:
                    raise UnknownCommandError(command_name)
                data = request.get_data()
                input_dict = json.loads(data)
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
        def usage(command_name):
            try:
                try:
                    command = self.commands[command_name]
                except KeyError:
                    raise UnknownCommandError(command_name)
                return json.dumps(to_long_spec(command))
            except RunwayError as err:
                return json.dumps(err.to_response())

    def parse_opts(self):
        parser = ArgumentParser()
        parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for the model server')
        parser.add_argument('--port', type=int, default=8000, help='Port for the model server')
        parser.add_argument('--rw_model_options', type=str, default=os.getenv(
            'RW_MODEL_OPTIONS', '{}'), help='Pass options to the Runway model as a JSON string')
        parser.add_argument('--debug', action='store_true',
                            help='Activate debug mode (live reload)')
        parser.add_argument('--manifest', action='store_true',
                            help='Print model manifest')
        args = parser.parse_args()
        return args

    def setup(self, decorated_fn=None, options=None):
        if decorated_fn:
            self.options = None
            self.setup_fn = decorated_fn
        else:
            def decorator(fn):
                self.options = options
                self.setup_fn = fn
                return fn
            return decorator

    def command(self, name, inputs=None, outputs=None):
        if inputs is None or outputs is None:
            raise Exception(
                'You need to provide inputs and outputs for the command')
        command_info = dict(inputs=inputs, outputs=outputs)
        self.commands[name] = command_info

        def decorator(fn):
            self.command_fns[name] = fn
            return fn
        return decorator

    def run(self):
        host = self.opts.host
        port = self.opts.port
        if self.opts.manifest:
            print(json.dumps(dict(options=self.options, commands=self.commands)))
            return
        print('Setting up model...')
        if self.setup_fn:
            try:
                setup_opts = json.loads(self.opts.rw_model_options)
                if self.options:
                    for opt_name, opt_type in self.options.items():
                        if opt_name not in setup_opts:
                            raise MissingOptionException(opt_name)
                    setup_opts[opt_name] = deserialize(
                            setup_opts[opt_name], opt_type)
                    self.model = self.setup_fn(setup_opts)
                else:
                    self.model = self.setup_fn()
            except Exception as err:
                print('Encountered error during setup:\n %s' % repr(err))
                _, _, tb = sys.exc_info()
                formatted_tb = ''.join(traceback.format_tb(tb))
                print(formatted_tb)
                sys.exit(1)
        print('Starting model server at http://{0}:{1}...'.format(host, port))
        self.started = datetime.datetime.utcnow().isoformat()
        if self.opts.debug:
            logging.basicConfig(level=logging.DEBUG)
            self.app.debug = True
            self.app.run(host=host, port=port, debug=True, threaded=True)
        else:
            http_server = WSGIServer((host, port), self.app)
            try:
                http_server.serve_forever()
            except KeyboardInterrupt:
                print('Stopping server...')
