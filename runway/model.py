import os
import sys
import logging
import datetime
import traceback
import inspect
import json
import gevent
import time
from multiprocessing import Process
from six import reraise
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sockets import Sockets
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from .exceptions import RunwayError, MissingInputError, MissingOptionError, \
    InferenceError, UnknownCommandError, SetupError
from .data_types import *
from .utils import gzipped, serialize_command, cast_to_obj, timestamp_millis, \
        validate_post_request_body_is_json, get_json_or_none_if_invalid, argspec, \
        deserialize_data, serialize_data, generate_uuid
from .__version__ import __version__ as model_sdk_version

class RunwayModel(object):
    """A Runway Model server. A singleton instance of this class is created automatically
       when the runway module is imported.
    """

    def __init__(self):
        self.millis_run_started_at = None
        self.millis_last_command = None
        self.options = []
        self.setup_fn = None
        self.commands = {}
        self.command_fns = {}
        self.jobs = {}
        self.model = None
        self.running_status = 'STARTING'
        self.app = Flask(__name__)
        self.sockets = Sockets(self.app)
        # Support utf-8 in application/json requests and responses.
        # We wrap this in a try/except block because, for whatever reason,
        # `make docs` throws a TypeError that keys are unassignable to
        # self.app.config. This DOES NOT occur when using the RunwayModel module
        # anywere except in the docs build environment.
        try: self.app.config['JSON_AS_ASCII'] = False
        except TypeError: pass
        CORS(self.app)
        self.define_error_handlers()
        self.define_routes()

    def define_error_handlers(self):

        # not yet implemented, but if and when it is lets make sure its returned
        # as JSON
        @self.app.errorhandler(401)
        def unauthorized(e):
            msg = 'Unauthorized (well... '
            msg += 'really unauthenticated but hey I didn\'t write the spec).'
            return jsonify(dict(error=msg)), 401

        # not yet implemented, but if and when it is lets make sure its returned
        # as JSON
        @self.app.errorhandler(403)
        def forbidden(e):
            return jsonify(dict(error='Forbidden.')), 403

        @self.app.errorhandler(404)
        def page_not_found(e):
            return jsonify(dict(error='Not found.')), 404

        @self.app.errorhandler(405)
        def method_not_allowed(e):
            return jsonify(dict(error='Method not allowed.')), 405

        # we shouldn't have any of these as we are wrapping errors in
        # RunwayError objects and returning stacktraces, but it can't hurt
        # to be safe.
        @self.app.errorhandler(500)
        def internal_server_error(e):
            return jsonify(dict(error='Internal server error.')), 500

    def define_routes(self):

        @self.app.route('/', methods=['GET'])
        @self.app.route('/meta', methods=['GET'])
        def manifest():
            return jsonify(dict(
                modelSDKVersion=model_sdk_version,
                millisRunning=self.millis_running(),
                millisSinceLastCommand=self.millis_since_last_command(),
                GPU=os.environ.get('GPU') == '1',
                options=[opt.to_dict() for opt in self.options],
                commands=[serialize_command(cmd) for cmd in self.commands.values()]
            ))

        @self.app.route('/healthcheck', methods=['GET'])
        def healthcheck_route():
            return jsonify(dict(status=self.running_status))

        @self.app.route('/setup', methods=['POST'])
        @validate_post_request_body_is_json
        def setup_route():
            opts = get_json_or_none_if_invalid(request)
            try:
                self.setup_model(opts)
                return jsonify(dict(success=True))
            except RunwayError as err:
                err.print_exception()
                return jsonify(err.to_response()), err.code

        @self.app.route('/setup', methods=['GET'])
        def setup_options_route():
            return jsonify(self.options)

        @self.app.route('/<command_name>', methods=['POST'])
        @validate_post_request_body_is_json
        def command_route(command_name):
            try:
                try:
                    command_fn = self.command_fns[command_name]
                except KeyError:
                    raise UnknownCommandError(command_name)
                inputs = self.commands[command_name]['inputs']
                outputs = self.commands[command_name]['outputs']
                input_dict = get_json_or_none_if_invalid(request)
                deserialized_inputs = deserialize_data(input_dict, inputs)
                self.millis_last_command = timestamp_millis()
                try:
                    if inspect.isgeneratorfunction(command_fn):
                        g = command_fn(self.model, deserialized_inputs)
                        try:
                            while True:
                                output_data = next(g)
                        except StopIteration as err:
                            if hasattr(err, 'value') and err.value is not None:
                                output_data = err.value
                    else:
                        output_data = command_fn(self.model, deserialized_inputs)
                except Exception as err:
                    raise reraise(InferenceError, InferenceError(repr(err)), sys.exc_info()[2])
                if type(output_data) == tuple:
                    output_data, _ = output_data
                return jsonify(serialize_data(output_data, outputs))
            except RunwayError as err:
                err.print_exception()
                return jsonify(err.to_response()), err.code
        
        @self.sockets.route('/')
        def inference_socket(ws):
            session_id = generate_uuid()
            self.jobs[session_id] = jobs_for_session = {}

            def send_message(job_id, message_type, data={}):
                ws.send(json.dumps(dict(type=message_type, id=job_id, **data)))

            def start_inference(job_id, command_name, input_dict):
                try:
                    try:
                        command_fn = self.command_fns[command_name]
                    except KeyError:
                        raise UnknownCommandError(command_name)

                    input_spec = self.commands[command_name]['inputs']
                    output_spec = self.commands[command_name]['outputs']
                    deserialized_inputs = deserialize_data(input_dict, input_spec)
                    time_start = timestamp_millis()

                    def send_output(output):
                        progress = None
                        if type(output) == tuple:
                            output, progress = output
                        output = serialize_data(output, output_spec)
                        to_send = {'outputData': output}
                        if progress is not None:
                            to_send['progress'] = progress
                        send_message(job_id, 'output', to_send)

                    if inspect.isgeneratorfunction(command_fn):
                        g = command_fn(self.model, deserialized_inputs)
                        try:
                            while True:
                                output = next(g)
                                send_output(output)
                        except StopIteration as err:
                            if hasattr(err, 'value') and err.value is not None:
                                send_output(err.value)
                        except Exception as err:
                            raise reraise(InferenceError, InferenceError(repr(err)), sys.exc_info()[2])
                    else:
                        try:
                            output = command_fn(self.model, deserialized_inputs)
                            send_output(output)
                        except Exception as err:
                            raise reraise(InferenceError, InferenceError(repr(err)), sys.exc_info()[2])

                    send_message(job_id, 'succeeded', {
                        'timeElapsed': timestamp_millis() - time_start
                    })

                except RunwayError as err:
                    send_message(job_id, 'failed', err.to_response())
                    err.print_exception()

                except Exception as err:
                    send_message(job_id, 'failed', {'error': 'An unknown error occurred'})
                    print(err)

            while not ws.closed:
                message = ws.receive()
                try:
                    message = json.loads(message)
                except:
                    continue

                if message['type'] == 'submit':
                    command_name = message['command']
                    input_dict = message['inputData']
                    self.millis_last_command = timestamp_millis()
                    if 'id' in message:
                        job_id = message['id']
                        if job_id in self.jobs:
                            continue
                    else:
                        job_id = generate_uuid()
                    job = self.jobs[job_id] = Process(target=start_inference, args=(job_id, command_name, input_dict))
                    job.start()
                    jobs_for_session[job_id] = job
                    send_message(job_id, 'started')

                elif message['type'] == 'cancel':
                    command_name = message['id']
                    if job_id in jobs_for_session:
                        jobs_for_session[job_id].terminate()
                        send_message(job_id, 'cancelled')

            for job in jobs_for_session.values():
                job.terminate()

        @self.app.route('/<command_name>', methods=['GET'])
        def usage_route(command_name):
            try:
                try:
                    command = self.commands[command_name]
                except KeyError:
                    raise UnknownCommandError(command_name)
                return jsonify(serialize_command(command))
            except RunwayError as err:
                err.print_exception()
                return jsonify(err.to_response()), err.code

    def millis_running(self):
        if self.millis_run_started_at is None: return None
        return timestamp_millis() - self.millis_run_started_at

    def millis_since_last_command(self):
        if self.millis_last_command is None: return None
        return timestamp_millis() - self.millis_last_command

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

            # Descriptions are used to document each data type; Their values appear in the app as
            # tooltips. Writing detailed descriptions for each model option goes a long way towards
            # helping users learn how to interact with your model. Write descriptions as full sentences.
            network_size_description = "The size of the network. A larger number will result in better accuracy at the expense of increased latency."
            options = { "network_size": category(choices=[64, 128, 256, 512], default=256, description=network_size_description) }
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

    def command(self, name, inputs={}, outputs={}, description=None):
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
                "z": vector(length=512, description="The seed used to generate an output image."),
                "category": category(choices=["day", "night"])
            }

            sample_outputs = {
                "image": image(width=1024, height=1024)
            }

            # Descriptions are used to document each data type and `@runway.command()`; Their values appear
            # in the app as tooltips. Writing detailed descriptions for each model option goes a long way
            # towards helping users learn how to interact with your model. Write descriptions as full
            # sentences.
            sample_description = "Generate a new image based on a z-vector and an output style: Day or night."
            @runway.command("sample",
                            inputs=sample_inputs,
                            outputs=sample_outputs,
                            description=sample_description)
            def sample(model, inputs):
                # The parameters passed to a function decorated by @runway.command() are:
                #   1. The return value of a function wrapped by @runway.setup(), usually a model.
                #   2. The inputs sent with the HTTP request to the /<command_name> endpoint,
                #      as defined by the inputs keyword argument delivered to @runway.command().
                img = model.sample(z=inputs["z"], category=inputs["category"])
                # `img` can be a PIL or numpy image. It will be encoded as a base64 URI string
                # automatically by @runway.command().
                return { "image": img }

        .. note::
            All ``@runway.command()`` decorators accept a ``description`` keyword argument
            that can be used to describe what the command does. Descriptions appear as
            tooltips in the app and help users learn what the command does. It's best
            practice to write full-sentence descriptions for each of your input variables
            and commands.

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
        :param description: A text description of what this command does.
            If this parameter is present its value will be rendered as a tooltip
            in Runway. Defaults to None.
        :type description: string, optional
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
            # It is the responsibility of the RunwayModel's setup() and command()
            # functions to assign names to runway.data_types based on the dictionary
            # keys
            inp_obj.name = input_name
            inputs_as_list.append(inp_obj)

        outputs_as_list = []
        for output_name, out in outputs.items():
            out_obj = cast_to_obj(out)
            out_obj.name = output_name
            outputs_as_list.append(out_obj)

        command_info = dict(
            name=name,
            description=description,
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
                elif hasattr(opt, 'default'):
                    deserialized_opts[name] = opt.default
                else:
                    raise MissingOptionError(name)
            try:
                self.model = self.setup_fn(deserialized_opts)
            except Exception as err:
                raise reraise(SetupError, SetupError(repr(err)), sys.exc_info()[2])
        elif self.setup_fn:
            try:
                if len(argspec(self.setup_fn).args) == 0:
                    self.model = self.setup_fn()
                else:
                    self.model = self.setup_fn({})
            except Exception as err:
                raise reraise(SetupError, SetupError(repr(err)), sys.exc_info()[2])
        self.running_status = 'RUNNING'

    def run(self, host='0.0.0.0', port=9000, model_options={}, debug=False, meta=False, no_serve=False):
        """Run the model and start listening for HTTP requests on the network.
        By default, the server will run on port ``9000`` and listen on all
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
        :param port: The port to bind the HTTP server to, defaults to ``9000``.
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
        :param no_serve: Don't start the Flask server, defaults to ``False``
            (i.e. the Flask server is started by default when the
            ``runway.run()`` function is called without setting this argument
            set to True). This functionality is used during automated testing to
            mock HTTP requests using Flask's ``app.test_client()``
            (see Flask's testing_ docs for more details).
        :type meta: boolean, optional

        .. _testing: http://flask.pocoo.org/docs/1.0/testing/

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
              and commands as JSON and then exits. This environment variable
              overwrites any value passed as the ``meta`` keyword argument.
            - ``RW_NO_SERVE``: Forces ``runway.run()`` to not start its Flask
              server. This environment variable overwrites any value passed as
              the ``no_serve`` keyword argument.
        """

        env_host          = os.getenv('RW_HOST')
        env_port          = os.getenv('RW_PORT')
        env_meta          = os.getenv('RW_META')
        env_debug         = os.getenv('RW_DEBUG')
        env_no_serve      = os.getenv('RW_NO_SERVE')
        env_model_options = os.getenv('RW_MODEL_OPTIONS')

        if env_host is not None:
            host = env_host
        if env_port is not None:
            port = int(env_port)
        if env_meta is not None:
            meta = bool(int(env_meta))
        if env_debug is not None:
            debug = bool(int(env_debug))
        if env_no_serve is not None:
            no_serve = bool(int(env_no_serve))
        if env_model_options is not None:
            model_options = json.loads(env_model_options)

        if meta:
            print(json.dumps(dict(
                options=[opt.to_dict() for opt in self.options],
                commands=[serialize_command(cmd) for cmd in self.commands.values()]
            )))
            return

        print('Initializing model...')

        initialization_start = time.time()
        try:
            self.setup_model(model_options)
        except RunwayError as err:
            err.print_exception()
            sys.exit(1)
        initialization_duration = time.time() - initialization_start
        if initialization_duration < 5:
            initialization_color = '\033[92m'
        elif initialization_duration < 10:
            initialization_color = '\033[93m'
        else:
            initialization_color = '\033[91m'
        print('Model initialized %s(%.2fs)\033[0m' % (
            initialization_color,
            initialization_duration,
        ))

        # start the run started at millis timer even if we don't actually serve
        self.millis_run_started_at = timestamp_millis()
        if no_serve:
            print('Not starting model server because "no_serve" directive is present.')
        else:
            print('Starting model server at http://{0}:{1}...'.format(host, port))
            if debug:
                logging.basicConfig(level=logging.DEBUG)
            else:
                logging.basicConfig(level=logging.INFO)
            http_server = WSGIServer((host, port), self.app, handler_class=WebSocketHandler)
            try:
                http_server.serve_forever()
            except KeyboardInterrupt:
                print('Stopping server...')
                for jobs_for_session in self.jobs.values():
                    for job in jobs_for_session.values():
                        job.terminate()
