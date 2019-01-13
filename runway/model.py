import json
from argparse import ArgumentParser
from flask import Flask, jsonify, request
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from .exceptions import RunwayError, MissingInputException
from .io import serialize, deserialize

class RunwayModel(object):
    def __init__(self):
        self.setup_fn = None
        self.commands = []
        self.model = None
        self.opts = self.parse_opts()
        self.app = Flask(__name__)
        CORS(self.app)

        @self.app.route('/healthcheck')
        def healthcheck():
            return jsonify(message='Model running')

        @self.app.route('/manifest')
        def manifest():
            return jsonify(commands=self.commands)

    def parse_opts(self):
        parser = ArgumentParser()
        parser.add_argument('--rw_setup_options', type=str, default='{}', help='Pass options to the Runway model as a JSON string')
        parser.add_argument('--debug', action='store_true', help='Activate debug mode (live reload)')
        args = parser.parse_args()
        return args

    def setup(self, fn):
        self.setup_fn = fn
        return fn

    def command(self, name, inputs=None, outputs=None):
        if inputs is None or outputs is None:
            raise Exception('You need to provide inputs and outputs for the command')
        command_info = dict(
            name=name,
            inputs=inputs,
            outputs=outputs
        )
        self.commands.append(command_info)
        def decorator(fn):
            @self.app.route('/' + name + '/usage')
            def usage_endpoint():
                return jsonify(command_info)

            @self.app.route('/' + name, methods=['POST'])
            def infer_endpoint():
                try:
                    input_dict = request.json
                    for input_name, input_type in inputs.items():
                        if input_name not in input_dict:
                            raise MissingInputException(input_name)
                        input_dict[input_name] = deserialize(
                            input_dict[input_name], input_type)
                    output_dict = fn(self.model, input_dict)
                    for output_name, output_type in outputs.items():
                        output_dict[output_name] = serialize(
                            output_dict[output_name], output_type)
                    return jsonify(output_dict)
                except RunwayError as err:
                    return jsonify(err.to_response())
            return fn
        return decorator

    def run(self, host='0.0.0.0', port=8000, threaded=True):
        print('Setting up model...')
        if self.setup_fn:
            setup_opts = json.loads(self.opts.rw_setup_options)
            self.model = self.setup_fn(**setup_opts)
        if self.opts.debug:
            self.app.debug = True
            self.app.run(host=host, port=port, debug=True)
        else:
            http_server = WSGIServer((host, port), self.app)
            print('Starting model server...')
            try:
                http_server.serve_forever()
            except KeyboardInterrupt:
                print('Stopping server...')
