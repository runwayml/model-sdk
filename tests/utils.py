from functools import wraps
from multiprocessing import Process
import errno
import os
import signal
import json
import time
from websocket import create_connection
from runway import RunwayModel 

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

class run_model_on_child_process():
    def __init__(self, model, startup_delay=1, *args, **kwargs):
        self.model = model
        self.args = args
        self.kwargs = kwargs
        self.startup_delay = startup_delay

    def __enter__(self):
        os.environ['RW_NO_SERVE'] = '0'
        self.proc = Process(target=self.model.run, args=self.args, kwargs=self.kwargs)
        self.proc.start()
        time.sleep(self.startup_delay)
        return self.proc

    def __exit__(self, *args):
        if self.proc:
            self.proc.terminate()
        os.environ['RW_NO_SERVE'] = '1'

class test_ws_client():
    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = create_connection('ws://localhost:9000/')
        return self.conn

    def __exit__(self, *args):
        if self.conn:
            self.conn.close()
