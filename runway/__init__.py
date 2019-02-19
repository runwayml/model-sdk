from .model import RunwayModel
import sys

__version__ = '0.1.0'

def setup(options):
    def decorator(fn):
        module = sys.modules[fn.__module__]
        setattr(module, 'runway_setup', fn)
        setattr(module, 'runway_setup_options', options)
        return fn
    return decorator

def command(name, inputs, outputs):
    def decorator(fn):
        module = sys.modules[fn.__module__]
        setattr(module, 'runway_command_count', getattr(module, 'runway_command_count', 0) + 1)
        setattr(module, 'runway_command_%d' % (getattr(module, 'runway_command_count') - 1), fn)
        setattr(module, 'runway_command_%d_options' % (getattr(module, 'runway_command_count') - 1), dict(name=name, inputs=inputs, outputs=outputs))
        return fn
    return decorator
