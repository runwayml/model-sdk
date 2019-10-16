from functools import wraps
import errno
import os
import signal
import json
from websocket import create_connection
from runway import RunwayModel

def get_test_client(rw_model):
    assert isinstance(rw_model, RunwayModel)
    rw_model.app.config['TESTING'] = True
    return rw_model.app.test_client()

def get_test_ws_client(rw_model):
    assert isinstance(rw_model, RunwayModel)
    return create_connection('ws://localhost:9000/')

def get_manifest(client):
    response = client.get('/meta')
    return json.loads(response.data)

def create_ws_message(message_type, data):
    return json.dumps(dict(type=message_type, **data))

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
