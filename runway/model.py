import os
import sys
import logging
import datetime
import traceback
import json
from six import reraise
from flask import Flask, request
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from .exceptions import RunwayError, MissingInputError, MissingOptionError, \
    InferenceError, UnknownCommandError, SetupError
from .data_types import *
from .utils import gzipped, serialize_command, cast_to_obj

class RunwayModel(object):
    """A Runway Model server. A singleton instance of this class is created automatically
       when the runway module is imported.
    """

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
                err.print_exception()
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
                    if name not in input_dict and getattr(inp, 'default', None) is None:
                        raise MissingInputError(name)
                    value = input_dict[name] or getattr(inp, 'default', None)
                    deserialized_inputs[name] = inp.deserialize(value)
                try:
                    results = command_fn(self.model, deserialized_inputs)
                    if type(results) != dict:
                        name = outputs[0].name
                        value = results
                        results = {}
                        results[name] = value
                except Exception as err:
                    raise reraise(InferenceError, InferenceError(repr(err)), sys.exc_info()[2])

                serialized_outputs = {}
                for out in outputs:
                    name = out.to_dict()['name']
                    serialized_outputs[name] = out.serialize(results[name])
                return json.dumps(serialized_outputs).encode('utf8')

            except RunwayError as err:
                err.print_exception()
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
                err.print_exception()
                return json.dumps(err.to_response())

    def setup(self, decorated_fn=None, options=None):
        """This decorator is used to wrap your own ``setup()`` (or equivalent)
        function to run whatever initialization code you'd like. Your wrapped
        function `should` configure and return a model. Your function `should`
        also be made resilient to being called multiple times, as this is
        possible depending on the behavior of the client application.

        This endpoint exposes a ``/setup`` HTTP route and calls the wrapped
        (decorated) function once on ``runway.run()`` and whenever a new POST
        request is made to the ``/setup`` route.

        .. code-block:: python

            import runway
            from runway.data_types import category
            from your_code import model

            options = {"network_size": category(choices=[64, 128, 256, 512], default=256)}
            @runway.setup(options=options)
            def setup(opts):
                print("Setup ran, and the network size is {}".format(opts["network_size"]))
                return model(network_size=opts["network_size"])

        .. note::
            This is example code for demonstration purposes only. It will not
            run, as the ``your_code`` import is not a real python module.

        :param decorated_fn: A function to be decorated. This argument is automatically
            assigned the value of the wrapped function if the decorator syntax is used
            without a function call
            (e.g. ``@runway.setup`` instead of ``@runway.setup()``).
        :type decorated_fn: function, optional
        :param options: A dictionary of setup options, mapping string names
            to ``runway.data_types``. These options define the schema of the
            object that is passed as the single argument to the wrapped
            function.
        :type options: dict, optional
        :return: A decorated function
        :rtype: function or `NoneType`
        """

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
        """This decorator function is used to define the interface for your
        model. All functions that are wrapped by this decorator become exposed
        via HTTP requests to ``/<command_name>``. Each command that you define
        can be used to get data into or out of your runway model, or trigger an
        action.

        .. code-block:: python

            import runway
            from runway.data_types import category, vector, image
            from your_code import model

            @runway.setup
            def setup():
                return model()

            sample_inputs= {
                "z": vector(length=512),
                "category": category(choices=["day", "night"])
            }

            sample_outputs = {
                "image": image(width=1024, height=1024)
            }

            @runway.command("sample", inputs=sample_inputs, outputs=sample_outputs)
            def sample(model, inputs):
                # The parameters passed to a function decorated by @runway.command() are:
                #   1. The return value of a function wrapped by @runway.setup(), usually a model.
                #   2. The inputs sent with the HTTP request to the /<command_name> endpoint,
                #      as defined by the inputs keyword argument delivered to @runway.command().
                img = model.sample(z=inputs["z"], category=inputs["category"])
                # `img` can be a PIL or numpy image. It will be encoded as a base64 URI string
                # automatically by @runway.command().
                return { "image": img }

        :param name: The name of the command. This name is used to create the
            HTTP route associated with the command
            (i.e. a name of "generate_text" will generate a ``/generate_text``
            route).
        :type name: string
        :param inputs: A dictionary mapping input names to
            ``runway.data_types``. This dictionary defines the interface used
            to send input data to this command. At least one key value pair is
            required.
        :type inputs: dict
        :param outputs: A dictionary defining the output data returned from the
            wrapped function as ``runway.data_types``. At least one key value
            pair is required.
        :type outputs: dict
        :raises Exception: An exception if there isn't at least one key value
            pair for both inputs and outputs dictionaries
        :return: A decorated function
        :rtype: function
        """
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
            try:
                self.model = self.setup_fn(deserialized_opts)
            except Exception as err:
                raise reraise(SetupError, SetupError(repr(err)), sys.exc_info()[2])
        elif self.setup_fn:
            self.model = self.setup_fn()
        self.running_status = 'RUNNING'

    def run(self, host='0.0.0.0', port=8000, model_options={}, debug=False, meta=False):
        """Run the model and start listening for HTTP requests on the network.
        By default, the server will run on port ``8000`` and listen on all
        network interfaces (``0.0.0.0``).

        .. code-block:: python

            import runway

            # ... setup an initialization function with @runway.setup()
            # ... define a command or two with @runway.command()

            # now it's time to run the model server which actually sets up the
            # routes and handles the HTTP requests.
            if __name__ == "__main__":
                runway.run()

        ``runway.run()`` acts as the entrypoint to the runway module. You should
        call it as the last thing in your ``runway_model.py``, once you've
        defined a ``@runway.setup()`` function and one or more
        ``@runway.command()`` functions.

        :param host: The IP address to bind the HTTP server to, defaults to
            ``"0.0.0.0"`` (all interfaces). This value will be overwritten by the
            ``RW_HOST`` environment variable if it is present.
        :type host: string, optional
        :param port: The port to bind the HTTP server to, defaults to ``8000``.
            This value will be overwritten by the ``RW_PORT`` environment
            variable if it is present.
        :type port: int, optional
        :param model_options: The model options that are passed to
            ``@runway.setup()`` during initialization, defaults to ``{}``. This
            value will be overwritten by the ``RW_MODEL_OPTIONS`` environment
            variable if it is present.
        :type model_options: dict, optional
        :param debug: Whether to run the Flask HTTP server in debug mode, which
            enables live reloading, defaults to ``False``. This value will be
            overwritten by the ``RW_DEBUG`` environment variable if it is
            present.
        :type debug: boolean, optional
        :param meta: Print the model's options and commands as JSON and exit,
            defaults to ``False``. This functionality is used in a production
            environment to dynamically discover the interface presented by
            the Runway model at runtime. This value will be overwritten by the
            ``RW_META`` environment variable if it is present.
        :type meta: boolean, optional

        .. warning::
            All keyword arguments to the ``runway.run()`` function will be
            overwritten by environment variables when your model is run by the
            Runway app. Using the default values for these arguments, or
            supplying your own in python code, is fine so long as you are aware
            of the fact that their values will be overwritten by the following
            environment variables at runtime in a production environment:

            - ``RW_HOST``: Defines the IP address to bind the HTTP server to.
              This environment variable overwrites any value passed as the
              ``host`` keyword argument.
            - ``RW_PORT``: Defines the port to bind the HTTP server to. This
              environment variable overwrites any value passed as the ``port``
              keyword argument.
            - ``RW_MODEL_OPTIONS``: Defines the model options that are passed to
              ``@runway.setup()`` during initialization. This environment
              variable overwrites any value passed as the ``model_options``
              keyword argument.
            - ``RW_DEBUG``: Defines whether to run the Flask HTTP server in
              debug mode, which enables live reloading. This environment
              variable overwrites any value passed as the ``debug`` keyword
              argument. ``RW_DEBUG=1`` enables debug mode.
            - ``RW_META``: Defines the behavior of the ``runway.run()``
              function. If ``RW_META=1`` the function prints the model's options
              and commands as JSON and then exits. This environment variables
              overwrites any value passed as the ``meta`` keyward argument.
        """

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
            err.print_exception()
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
