import base64
import io
import json
from argparse import ArgumentParser
from flask import Flask, jsonify, request
from flask_cors import CORS
from .exceptions import RunwayError, MissingInputException
from .io import serialize, deserialize

class RunwayModel(object):
    def __init__(self):
        self.setup_fn = None
        self.model = None
        self.app = Flask(__name__)
        CORS(self.app)

        @self.app.route('/healthcheck')
        def healthcheck():
            return jsonify(message='Model running')

    def parse_opts(self):
        parser = ArgumentParser()
        parser.add_argument('--rw_setup_options', type=str, default='{}')
        args = parser.parse_args()
        return json.loads(args.rw_setup_options)

    def setup(self, fn):
        self.setup_fn = fn
        return fn

    def command(self, path, inputs=None, outputs=None):
        if inputs is None or outputs is None:
            raise Exception('You need to provide inputs and outputs for the command')
        def decorator(fn):
            @self.app.route('/' + path, methods=['POST'])
            def http_endpoint():
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
        if self.setup_fn:
            opts = self.parse_opts()
            self.model = self.setup_fn(opts)
        self.app.run(host=host, port=port, threaded=threaded)
