from .model import RunwayModel
from .data_types import *
from .__version__ import __version__

__defaultmodel__ = RunwayModel()
setup = __defaultmodel__.setup
command = __defaultmodel__.command
run = __defaultmodel__.run