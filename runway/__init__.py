from .model import RunwayModel
from .data_types import *
import sys

__version__ = '0.1.0'

__defaultmodel__ = RunwayModel()
setup = __defaultmodel__.setup
command = __defaultmodel__.command
run = __defaultmodel__.run