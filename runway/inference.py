from multiprocessing import Process, Queue
import inspect
import sys
from .exceptions import InferenceError
from .utils import timestamp_millis

class InferenceJob(object):
    def __init__(self, command_fn, model, inputs):
        self.model = model
        self.inputs = inputs
        self.command_fn = command_fn
        self.queue = Queue()
        self.process = Process(target=self.run_inference)
        self.data = {}
        self.cancelled = False

    def start(self):
        self.process.start()

    def run_inference(self):
        def send_output(output):
            progress = None
            if type(output) == tuple:
                output, progress = output
            to_send = {'data': output}
            if progress is not None:
                to_send['progress'] = progress
            to_send['lastUpdated'] = timestamp_millis()
            self.queue.put(to_send)

        def send_error(error):
            self.queue.put(dict(**error.to_response(), lastUpdated=timestamp_millis()))

        if inspect.isgeneratorfunction(self.command_fn):
            g = self.command_fn(self.model, self.inputs)
            try:
                while True:
                    output = next(g)
                    send_output(output)
            except StopIteration as err:
                if hasattr(err, 'value') and err.value is not None:
                    send_output(err.value)
            except Exception as err:
                error = InferenceError(repr(err))
                send_error(error)
        else:
            try:
                output = self.command_fn(self.model, self.inputs)
                send_output(output)
            except Exception as err:
                error = InferenceError(repr(err))
                send_error(error)
        
    def cancel(self):
        self.cancelled = True
        self.process.terminate()

    def refresh_data(self):
        while not self.queue.empty():
            self.data = self.queue.get_nowait()
        return self.data

    def get(self):
        self.refresh_data()
        if self.cancelled:
            return dict(status='CANCELLED', **self.data)
        elif self.process.exitcode is None:
            return dict(status='RUNNING', **self.data)
        elif self.process.exitcode == 0:
            status = 'FAILED' if 'error' in self.data else 'SUCCEEDED'
            return dict(status=status, **self.data)
        else:
            return dict(status='FAILED', error='An unknown error occurred during inference.')
