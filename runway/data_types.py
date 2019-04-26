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
from .utils import is_url, download_to_temp_dir, try_cast_np_scalar, random_color_map
from .exceptions import MissingArgumentError, InvalidArgumentError


class any(object):
    """A generic data type. The value this data type takes must be serializable to JSON.

    .. code-block:: python

        import yaml
        import runway
        from runway.data_types import any
        from your_code import model

        # an example of passing your own yaml configuration using an "any" data_type and PyYAML
        @runway.setup(options={ "configuration": any(name="yaml") })
        def setup(opts):
            # parse the configuration string as yaml, and then pass the resulting
            # object as the configuration to your model
            config = yaml.load(opts["configuration"])
            return model(config)

    :param name: The name associated with this variable, defaults to "field"
    :type name: string, optional
    """

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
    """A data type representing an array (list) of other runway.data_type objects.

    .. code-block:: python

        import runway
        from runway.data_types import array, text

        @runway.setup(options={ "seed_sentences": array(item_type=text, min_length=5) })
        def setup(opts):
            for i in range(5):
                print("Sentence {} is \"{}\"".format(i+1, opts["seed_sentences"][i]))

    :param item_type: A runway.data_type class, or an instance of a runway.data_type class
    :type item_type: runway.data_type
    :param name: The name associated with this variable, defaults to "{item_type}_array" \
        (e.g. "image_array")
    :type name: string, optional
    :param min_length: The minimum number of elements required to be in the array, defaults to 0
    :type min_length: int, optional
    :param max_length: The maximum number of elements allowed to be in the array, defaults to None
    :type max_length: int, optional
    :raises MissingArgumentError: A missing argument error if item_type is not specified
    """
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
    """A data type representing an image. Images represent PIL or numpy
    images but are passed to and from the Model SDK as base64 encoded data URI
    strings over the network
    (e.g. ``data:image/jpeg;base64,/9j/2wCEAAgGBgcG...``).

    When using an image as an output data type for a function wrapped by ``@runway.command()``,
    return a PIL or numpy image from your wrapped function and it will automatically
    be serialized as a base64 encoded data URI.

    .. code-block:: python

        import runway
        from runway.data_types import image

        inputs = {"image": image(width=512, height=512)}
        outputs = {"image": image(width=512, height=512)}
        @runway.command("style_transfer", inputs=inputs, outputs=outputs)
        def style_transfer(result_of_setup, args):
            # perform some transformation to the image, and then return it as a
            # PIL image or numpy image
            img = do_style_transfer(args["image"])
            # The PIL or numpy image will be automatically converted to a base64
            # encoded data URI string by the @runway.command() decorator.
            return { "image": img }

    :param name: The name associated with this variable, defaults to "image"
    :type name: string, optional
    :param channels: The number of channels in the image, defaults to 3. \
        E.g. an "rgb" image has 3 channels while an "rgba" image has 4.
    :type channels: int, optional
    :param min_width: The minimum width of the image, defaults to None
    :type min_width: int, optional
    :param min_height: The minimum height of the image, defaults to None
    :type min_height: int, optional
    :param max_width: The maximum width of the image, defaults to None
    :type max_width: int, optional
    :param max_height: The maximum height of the image, defaults to None
    :type max_height: int, optional
    :param width: The width of the image, defaults to None.
    :type width: int, optional
    :param height: The height of the image, defaults to None
    :type height: int, optional
    """
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
        elif issubclass(type(value), Image.Image):
            im_pil = value
        else:
            raise InvalidArgumentError('value is not a PIL or numpy image')
        buffer = IO()
        im_pil.save(buffer, format='JPEG')
        return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('utf8')

    def to_dict(self):
        ret = {}
        ret['type'] = 'image'
        ret['name'] = self.name
        ret['channels'] = self.channels
        if self.min_width: ret['minWidth'] = self.min_width
        if self.max_width: ret['maxWidth'] = self.max_width
        if self.min_height: ret['minHeight'] = self.min_height
        if self.max_height: ret['maxHeight'] = self.max_height
        if self.width: ret['width'] = self.width
        if self.height: ret['height'] = self.height
        return ret


class vector(object):
    """A data type representing a vector of floats.

    .. code-block:: python

        import runway
        from runway.data_types import vector, number
        import numpy as np

        inputs={"length": number(min=1)}
        outputs={"vector": vector(length=512)}
        @runway.command("random_sample", inputs=inputs, outputs=outputs)
        def random_sample(result_of_setup, args):
            vec = vector(length=args["length"])
            rand = np.random.random_sample(args["length"])
            return { "vector": vec.deserialize(rand) }

    :param length: The number of elements in the vector
    :type length: int
    :param name: The name associated with this variable, defaults to "vector"
    :type name: string, optional
    :param sampling_mean: The mean of the sample the vector is drawn from, defaults to 0
    :type sampling_mean: float, optional
    :param sampling_std: The standard deviation of the sample the vector is drawn from, defaults to 1
    :type sampling_std: float, optional
    :raises MissingArgumentError: A missing argument error if length is not specified
    """
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
    """A categorical data type that allows you to specify a variable's value \
        as a member of a set list of choices.

        .. code-block:: python

            import runway
            from runway.data_types import category

            # if no default value is specified, the first element in the choices
            # list will be used
            cat = category(choices=["rgb", "bgr", "rgba", "bgra"], default="rgba")
            @runway.setup(options={ "pixel_order": cat })
            def setup(opts):
                print("The selected pixel order is {}".format(opts["pixel_order"]))

        :param name: The name associated with this variable, defaults to "category"
        :type name: string, optional
        :param choices: A list of categories, defaults to None
        :type choices: A list of strings
        :param default: A default list of categories, defaults to None
        :type default: A list of strings
        :raises MissingArgumentError: A missing argument error if choices is
            not a list with at least one element.
        :raises InvalidArgumentError: An invalid argument error if a default
            argument is specified and that argument does not appear in the
            choices list.
    """

    def __init__(self, name=None, choices=None, default=None):
        if choices is None or len(choices) == 0: raise MissingArgumentError('choices')
        if default is not None and default not in choices:
            msg = 'default argument {} is not in choices list'.format(default)
            raise InvalidArgumentError(msg)
        self.name = name or 'category'
        self.choices = choices
        self.default = default or self.choices[0]

    def deserialize(self, value):
        if value not in self.choices:
            raise InvalidArgumentError(self.name)
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
    """A basic number data type. Instantiate this class to create a new runway model variable.

    .. code-block:: python

        import runway
        from runway.data_types import number

        @runway.setup(options={ "number_of_samples": number })
        def setup(opts):
            print("The number of samples is {}".format(opts["number_of_samples"]))

    :param name: The name associated with this variable, defaults to None
    :type name: string, optional
    :param default: A default value for this number variable, defaults to 0
    :type default: float, optional
    :param min: The minimum allowed value of this number type, defaults to 0
    :type min: float, optional
    :param max: The maximum allowed value of this number type, defaults to 1
    :type max: float, optional
    :param step: The step size of this number type. This argument define the minimum change \
        of value associated with this number type. E.g., a step size of `0.1` would allow this data \
        type to take on the values ``[0.0, 0.1, 0.2, ..., 1.0]``. Defaults to 1.
    :type step: float, optional
    """

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
    """A basic text data type. Used to represent strings. \
        Instantiate this class to create a new runway model variable.

    .. code-block:: python

        import runway
        from runway.data_types import text

        @runway.setup(options={ "flavor": text(default="vanilla") })
        def setup(opts):
            print("The selected flavor is {}".format(opts["flavor"]))

    :param name: The name associated with this variable, defaults to "text"
    :type name: string, optional
    :param default: The default value for this text variable, defaults to ''
    :type default: str, optional
    :param min_length: The minimum character length of this text variable, defaults to 0
    :type min_length: int, optional
    :param max_length: The maximum character length of this text variable, \
        defaults to None, which allows text to be of any maximum length
    :type max_length: int, optional
    """
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
    """A data type that represents a file or folder. The file can be a local \
        resource on disk or a remote resource loaded over HTTP. \
        Instantiate this class to create a new runway model variable.

    .. code-block:: python

        import runway
        from runway.data_types import file, category

        inputs = {"folder": file(is_folder=True)}
        outputs = {"result": category(choices=["success", "failure"])}
        @runway.command("batch_process", inputs=inputs, outputs=outputs)
        def batch_process(result_of_setup, args):
            result = do_something_with(args["folder"])
            return { "result": "success" if result else "failure" }

    :param name: The name of this variable, defaults to None
    :type name: string, optional
    :param is_folder: Does this variable represent a folder instead of a file? Defaults to False.
    :type is_folder: bool, optional
    """

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


class semantic_map(object):
    def __init__(self, name=None, default_label=None, label_map=None, color_map=None, width=None, height=None):
        if label_map is None:
            raise MissingArgumentError('label_map')
        if type(label_map) is not dict or len(label_map.keys()) == 0:
            msg = 'label_map argument has invalid type'
            raise InvalidArgumentError(msg)
        if default_label is not None and default_label not in label_map.values():
            msg = 'default_label {} is not in label map'.format(default_label)
            raise InvalidArgumentError(msg)
        if color_map and set(color_map.keys()) != set(label_map.values()):
            msg = 'color_map argument does not cover all labels'
            raise InvalidArgumentError(msg)
        self.name = name or 'semantic_map'
        self.label_map = label_map
        self.default_label = default_label or list(self.label_map.values())[0]
        self.color_map = color_map or self.generate_color_map()
        self.width = width
        self.height = height

    def generate_color_map(self):
        colors = random_color_map(len(self.label_map.keys()))
        color_map = {}
        for label, color in zip(self.label_map.values(), colors):
            color_map[label] = color
        return color_map

    def deserialize(self, value):
        return np.array(value)

    def serialize(self, value):
        return value.tolist()

    def to_dict(self):
        ret = {}
        ret['type'] = 'semantic_map'
        ret['name'] = self.name
        ret['defaultLabel'] = self.default_label
        ret['labelMap'] = self.label_map
        ret['colorMap'] = self.color_map
        ret['width'] = self.width
        ret['height'] = self.height
        return ret
