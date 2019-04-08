import sys
import math
import base64
import inspect
import json
if sys.version_info[0] < 3:
    from cStringIO import StringIO as IO
else:
    from io import BytesIO as IO
import numpy as np
from PIL import Image
from .utils import is_url, download_to_temp_dir, try_cast_np_scalar
from .exceptions import MissingArgumentError, InvalidInputError


class any(object):
    def __init__(self, name=None):
        self.name = name
    
    def serialize(self, v):
        return v

    def deserialize(self, v):
        return v

    def to_dict(self):
        ret = {}
        ret['type'] = 'any'
        ret['name'] = self.name or 'field'
        return ret        


class array(object):
    def __init__(self, item_type=None, name=None, min_length=0, max_length=None):
        if item_type is None: raise MissingArgumentError('item_type')
        if inspect.isclass(item_type):
            self.item_type = item_type()
        else:
            self.item_type = item_type
        self.name = name or '%s_array' % self.item_type.name
        self.min_length = min_length
        self.max_length = max_length

    def deserialize(self, items):
        return [self.item_type.deserialize(item) for item in items]

    def serialize(self, items):
        return [self.item_type.serialize(item) for item in items]

    def to_dict(self):
        ret = {}
        ret['name'] = self.name
        ret['type'] = 'array'
        ret['itemType'] = self.item_type.to_dict()
        ret['minLength'] = self.min_length
        if self.max_length: ret['maxLength'] = self.max_length
        return ret


class image(object):
    def __init__(self, name=None, channels=3, min_width=None, min_height=None, max_width=None, max_height=None, width=None, height=None):
        self.name = name or 'image'
        self.channels = channels
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
        self.width = width
        self.height = height

    def deserialize(self, value):
        image = value[value.find(",")+1:]
        image = base64.decodestring(image.encode('utf8'))
        buffer = IO(image)
        return Image.open(buffer)

    def serialize(self, value):
        if type(value) is np.ndarray:
            im_pil = Image.fromarray(value)
        elif type(value) is Image.Image:
            im_pil = value
        buffer = IO()
        im_pil.save(buffer, format='JPEG')
        return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('utf8')

    def to_dict(self):
        ret = {}
        ret['type'] = 'image'
        ret['name'] = self.name
        ret['channels'] = self.channels
        if self.min_width: ret['minWidth'] = self.min_width
        if self.max_width: ret['maxHeight'] = self.max_width
        if self.min_height: ret['minHeight'] = self.min_height
        if self.max_height: ret['maxHeight'] = self.max_height
        if self.width: ret['width'] = self.width
        if self.height: ret['height'] = self.height
        return ret


class vector(object):
    def __init__(self, length=None, name=None, sampling_mean=0, sampling_std=1):
        if length is None: raise MissingArgumentError('length')
        self.name = name or 'vector'
        self.length = length
        self.sampling_mean = sampling_mean
        self.sampling_std = sampling_std

    def deserialize(self, value):
        return np.array(value)

    def serialize(self, value):
        return value.tolist()

    def to_dict(self):
        ret = {}
        ret['type'] = 'vector'
        ret['name'] = self.name
        ret['length'] = self.length
        ret['samplingMean'] = self.sampling_mean
        ret['samplingStd'] = self.sampling_std
        return ret


class category(object):
    def __init__(self, name=None, choices=None, default=None):
        if choices is None or len(choices) == 0: raise MissingArgumentError('choices')
        self.name = name or 'category'
        self.choices = choices
        self.default = default or self.choices[0]

    def deserialize(self, value):
        if value not in self.choices:
            raise InvalidInputError(self.name)
        return value

    def serialize(self, value):
        return value

    def to_dict(self):
        ret = {}
        ret['type'] = 'category'
        ret['name'] = self.name
        ret['oneOf'] = self.choices
        ret['default'] = self.default
        return ret


class number(object):
    def __init__(self, name=None, default=0, min=0, max=1, step=1):
        self.name = name or 'number'
        self.default = default
        self.min = min
        self.max = max
        self.step = step

    def deserialize(self, value):
        return value

    def serialize(self, value):
        return try_cast_np_scalar(value)
    
    def to_dict(self):
        ret = {}
        ret['type'] = 'number'
        ret['name'] = self.name
        ret['default'] = self.default
        ret['min'] = self.min
        ret['max'] = self.max
        ret['step'] = self.step
        return ret


class text(object):
    def __init__(self, name=None, default='', min_length=0, max_length=None):
        self.name = name or 'text'
        self.default = default
        self.min_length = min_length
        self.max_length = max_length

    def deserialize(self, value):
        return value

    def serialize(self, value):
        return str(value)

    def to_dict(self):
        ret = {}
        ret['type'] = 'text'
        ret['name'] = self.name
        ret['default'] = self.default
        ret['minLength'] = self.min_length
        if self.max_length: ret['maxLength'] = self.max_length
        return ret


class file(object):
    def __init__(self, name=None, is_folder=False):
        self.name = name or 'file'
        self.is_folder = is_folder

    def deserialize(self, value):
        if is_url(value):
            return download_to_temp_dir(value)
        return value

    def serialize(self, value):
        return value

    def to_dict(self):
        ret = {}
        ret['type'] = 'file'
        ret['name'] = self.name
        if self.is_folder: ret['isFolder'] = self.is_folder
        return ret
