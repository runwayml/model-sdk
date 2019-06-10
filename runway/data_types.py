import sys
import math
import base64
import inspect
import json
import os
import tarfile
if sys.version_info[0] < 3:
    from cStringIO import StringIO as IO
else:
    from io import BytesIO as IO
import numpy as np
from PIL import Image
from .utils import is_url, extract_tarball, try_cast_np_scalar, download_file, get_color_palette
from .exceptions import MissingArgumentError, InvalidArgumentError

class BaseType(object):
    """An abstract class that defines a base data type interface. This type
    should be used as the base class of new data types, never directly.

    :param data_type: The data type represented as a string
    :type data_type: string
    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    """

    def __init__(self, data_type, description=None):
        self.type = data_type
        self.description = description

        # The name property is assigned after contruction through direct
        # property assignment (e.g. `txt = text(); txt.name = 'some_name' `)
        # It is the responsibility of the RunwayModel's setup() and command()
        # functions to assign names to runway.data_types based on the dictionary
        # keys
        self.name = None

    def serialize(self, value):
        raise NotImplementedError()

    def deserialize(self, value):
        raise NotImplementedError()

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description
        }

class any(BaseType):
    """A generic data type. The value this data type takes must be serializable to JSON.

    .. code-block:: python

        import yaml
        import runway
        from runway.data_types import any
        from your_code import model

        # an example of passing your own yaml configuration using an "any" data_type and PyYAML
        @runway.setup(options={ "configuration": any() })
        def setup(opts):
            # parse the configuration string as yaml, and then pass the resulting
            # object as the configuration to your model
            config = yaml.load(opts["configuration"])
            return model(config)

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    """

    def __init__(self, description=None):
        super(any, self).__init__('any', description=description)

    def serialize(self, v):
        return v

    def deserialize(self, v):
        return v

    def to_dict(self):
        return super(any, self).to_dict()

class array(BaseType):
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
    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    :param min_length: The minimum number of elements required to be in the array, defaults to 0
    :type min_length: int, optional
    :param max_length: The maximum number of elements allowed to be in the array, defaults to None
    :type max_length: int, optional
    :raises MissingArgumentError: A missing argument error if item_type is not specified
    """
    def __init__(self, item_type=None, description=None, min_length=0, max_length=None):
        super(array, self).__init__('array', description=description)
        if item_type is None: raise MissingArgumentError('item_type')
        if inspect.isclass(item_type):
            self.item_type = item_type()
        else:
            self.item_type = item_type
        self.item_type.name = '%s_array_item' % self.item_type.type
        self.min_length = min_length
        self.max_length = max_length

    def deserialize(self, items):
        return [self.item_type.deserialize(item) for item in items]

    def serialize(self, items):
        return [self.item_type.serialize(item) for item in items]

    def to_dict(self):
        ret = super(array, self).to_dict()
        ret['itemType'] = self.item_type.to_dict()
        ret['minLength'] = self.min_length
        if self.max_length: ret['maxLength'] = self.max_length
        return ret


class image(BaseType):
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

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
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
    def __init__(self, description=None, channels=3, min_width=None, min_height=None, max_width=None, max_height=None, width=None, height=None):
        super(image, self).__init__('image', description=description)
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
            raise InvalidArgumentError(self.name or self.type, 'value is not a PIL or numpy image')
        buffer = IO()
        im_pil.save(buffer, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('utf8')

    def to_dict(self):
        ret = super(image, self).to_dict()
        ret['channels'] = self.channels
        if self.min_width: ret['minWidth'] = self.min_width
        if self.max_width: ret['maxWidth'] = self.max_width
        if self.min_height: ret['minHeight'] = self.min_height
        if self.max_height: ret['maxHeight'] = self.max_height
        if self.width: ret['width'] = self.width
        if self.height: ret['height'] = self.height
        return ret


class vector(BaseType):
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

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    :param length: The number of elements in the vector
    :type length: int, inferred if a default vector is specified
    :param sampling_mean: The mean of the sample the vector is drawn from, defaults to 0
    :type sampling_mean: float, optional
    :param sampling_std: The standard deviation of the sample the vector is drawn from, defaults to 1
    :type sampling_std: float, optional
    :raises MissingArgumentError: A missing argument error if length is not specified
    """
    def __init__(self, description=None, length=None, default=None, sampling_mean=0, sampling_std=1):
        super(vector, self).__init__('vector', description=description)
        if default is not None:
            if length is None:
                length = len(default)
            elif len(default) != length:
                msg = 'default argument does not match expected length'
                raise InvalidArgumentError(self.name or self.type, msg)
        if length is None:
            raise MissingArgumentError('length')
        self.length = length
        self.sampling_mean = sampling_mean
        self.sampling_std = sampling_std
        self.default = default or np.full((length,), sampling_mean).tolist()

    def deserialize(self, value):
        return np.array(value)

    def serialize(self, value):
        return value.tolist()

    def to_dict(self):
        ret = super(vector, self).to_dict()
        ret['length'] = self.length
        ret['samplingMean'] = self.sampling_mean
        ret['samplingStd'] = self.sampling_std
        ret['default'] = self.default
        return ret


class category(BaseType):
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

        :param description: A description of this variable and how its used in the model,
            defaults to None
        :type description: string, optional
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

    def __init__(self, description=None, choices=None, default=None):
        super(category, self).__init__('category', description=description)
        if choices is None or len(choices) == 0: raise MissingArgumentError('choices')
        if default is not None and default not in choices:
            msg = 'default argument {} is not in choices list'.format(default)
            raise InvalidArgumentError(self.name or self.type, msg)
        self.choices = choices
        self.default = default or self.choices[0]

    def deserialize(self, value):
        if value not in self.choices:
            msg = 'category value "%s" does not appear in choices list.' % value
            raise InvalidArgumentError(self.name or self.type, msg)
        return value

    def serialize(self, value):
        return value

    def to_dict(self):
        ret = super(category, self).to_dict()
        ret['oneOf'] = self.choices
        ret['default'] = self.default
        return ret


class number(BaseType):
    """A basic number data type. Instantiate this class to create a new runway model variable.

    .. code-block:: python

        import runway
        from runway.data_types import number

        @runway.setup(options={ "number_of_samples": number })
        def setup(opts):
            print("The number of samples is {}".format(opts["number_of_samples"]))

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
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

    def __init__(self, description=None, default=0, min=0, max=1, step=1):
        super(number, self).__init__('number', description=description)
        self.default = default
        self.min = min
        self.max = max
        self.step = step

    def deserialize(self, value):
        return value

    def serialize(self, value):
        return try_cast_np_scalar(value)

    def to_dict(self):
        ret = super(number, self).to_dict()
        ret['default'] = self.default
        ret['min'] = self.min
        ret['max'] = self.max
        ret['step'] = self.step
        return ret


class text(BaseType):
    """A basic text data type. Used to represent strings. \
        Instantiate this class to create a new runway model variable.

    .. code-block:: python

        import runway
        from runway.data_types import text

        @runway.setup(options={ "flavor": text(default="vanilla") })
        def setup(opts):
            print("The selected flavor is {}".format(opts["flavor"]))

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    :param default: The default value for this text variable, defaults to ''
    :type default: string, optional
    :param min_length: The minimum character length of this text variable, defaults to 0
    :type min_length: int, optional
    :param max_length: The maximum character length of this text variable, \
        defaults to None, which allows text to be of any maximum length
    :type max_length: int, optional
    """
    def __init__(self, description=None, default='', min_length=0, max_length=None):
        super(text, self).__init__('text', description=description)
        self.default = default
        self.min_length = min_length
        self.max_length = max_length

    def deserialize(self, value):
        return value

    def serialize(self, value):
        return str(value)

    def to_dict(self):
        ret = super(text, self).to_dict()
        ret['default'] = self.default
        ret['minLength'] = self.min_length
        if self.max_length: ret['maxLength'] = self.max_length
        return ret


class file(BaseType):
    """A data type that represents a file or directory. The file can be a local \
        resource on disk or a remote resource loaded over HTTP. \
        Instantiate this class to create a new runway model variable.

    .. code-block:: python

        import runway
        from runway.data_types import file, category

        inputs = {"directory": file(is_directory=True)}
        outputs = {"result": category(choices=["success", "failure"])}
        @runway.command("batch_process", inputs=inputs, outputs=outputs)
        def batch_process(result_of_setup, args):
            result = do_something_with(args["directory"])
            return { "result": "success" if result else "failure" }

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    :param is_directory: Does this variable represent a directory instead of a file? Defaults to False.
    :type is_directory: bool, optional
    :param extension: Accept only files of this extension.
    :type extension: string, optional
    """

    def __init__(self, description=None, is_directory=False, extension=None):
        super(file, self).__init__('file', description=description)
        self.is_directory = is_directory
        self.extension = extension

    def deserialize(self, path_or_url):
        if is_url(path_or_url):
            downloaded_path = download_file(path_or_url)
            if tarfile.is_tarfile(downloaded_path):
                return extract_tarball(downloaded_path)
            else:
                return downloaded_path
        else:
            if not os.path.exists(path_or_url):
                raise InvalidArgumentError(self.name or self.type, 'file path provided does not exist')
            if self.extension and not path_or_url.endswith(self.extension):
                raise InvalidArgumentError(self.name or self.type, 'file path does not have expected extension')
            return path_or_url

    def serialize(self, value):
        return value

    def to_dict(self):
        ret = super(file, self).to_dict()
        if self.is_directory: ret['isDirectory'] = self.is_directory
        if self.extension: ret['extension'] = self.extension
        return ret


class segmentation(BaseType):
    """A datatype that represents a pixel-level segmentation of an image.
    Each pixel is annotated with a label id from 0-255, each corresponding to a
    different object class.
    When used as an input data type, `segmentation` accepts either a two-dimensional array,
    a 1-channel base64-encoded PNG image, or a 3-channel base64-encoded PNG colormap image.
    When used as an output data type, it serializes as a 1-channel base64-encoded PNG image.

    .. code-block:: python

        import runway
        from runway.data_types import segmentation, image

        inputs = {"segmentation_map": segmentation(label_to_id={"background": 0, "person": 1})}
        outputs = {"image": image()}
        @runway.command("synthesize_pose", inputs=inputs, outputs=outputs)
        def synthesize_human_pose(model, args):
            result = model.convert(args["segmentation_map"])
            return { "image": result }

    :param description: A description of this variable and how its used in the model,
        defaults to None
    :type description: string, optional
    :param label_to_id: A mapping from labels to pixel values from 0-255 corresponding to those labels
    :type label_to_id: dict
    :param default_label: The default label to use when a pixel value not in `label_to_id` is encountered
    :type default_label: string, optional
    :param label_to_color: A mapping from label names to colors to represent those labels
    :type label_to_color: dict, optional
    :param min_width: The minimum width of the segmentation image, defaults to None
    :type min_width: int, optional
    :param min_height: The minimum height of the segmentation image, defaults to None
    :type min_height: int, optional
    :param max_width: The maximum width of the segmentation image, defaults to None
    :type max_width: int, optional
    :param max_height: The maximum height of the segmentation image, defaults to None
    :type max_height: int, optional
    :param width: The width of the segmentation image, defaults to None.
    :type width: int, optional
    :param height: The height of the segmentation image, defaults to None
    :type height: int, optional
      """
    def __init__(self, description=None, label_to_id=None, label_to_color=None, default_label=None, min_width=None, min_height=None, max_width=None, max_height=None, width=None, height=None):
        super(segmentation, self).__init__('segmentation', description=description)
        if label_to_id is None:
            raise MissingArgumentError('label_to_id')
        if type(label_to_id) is not dict or len(label_to_id.keys()) == 0:
            msg = 'label_to_id argument has invalid type'
            raise InvalidArgumentError(msg)
        if default_label is not None and default_label not in label_to_id.keys():
            msg = 'default_label {} is not in label map'.format(default_label)
            raise InvalidArgumentError(msg)
        self.label_to_id = label_to_id
        self.label_to_color = self.complete_colors(label_to_color or {})
        self.default_label = default_label or list(self.label_to_id.keys())[0]
        self.width = width
        self.height = height
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height

    def complete_colors(self, seed_colors):
        colors = {}
        palette = get_color_palette('glasbey_bw')
        for label, label_id  in self.label_to_id.items():
            if label in seed_colors:
                colors[label] = seed_colors[label]
            else:
                colors[label] = palette[label_id]
        return colors

    def colormap_to_segmentation(self, img):
        cmap = np.array(img)[:, :, :3]
        seg = np.zeros(cmap.shape[:2], dtype=np.uint8)
        for label, color in self.label_to_color.items():
            label_id = self.label_to_id[label]
            seg[(cmap==color).all(axis=2)] = label_id
        return Image.fromarray(seg, 'L')

    def deserialize(self, value):
        if type(value) == list:
            return Image.fromarray(np.array(value).astype(np.uint8), 'L')
        else:
            try:
                image = value[value.find(",")+1:]
                image = base64.decodestring(image.encode('utf8'))
                buffer = IO(image)
                img = Image.open(buffer)
                if img.mode.startswith('RGB'):
                    return self.colormap_to_segmentation(img)
                else:
                    return img
            except:
                msg = 'unable to parse expected base64-encoded image'
                raise InvalidArgumentError(msg)

    def serialize(self, value):
        if type(value) is np.ndarray:
            im_pil = Image.fromarray(value)
        elif issubclass(type(value), Image.Image):
            im_pil = value
        else:
            raise InvalidArgumentError(self.name or self.type, 'value is not a PIL or numpy image')
        buffer = IO()
        im_pil.save(buffer, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('utf8')

    def to_dict(self):
        ret = super(segmentation, self).to_dict()
        ret['labels'] = list(self.label_to_id.keys())
        ret['defaultLabel'] = self.default_label
        ret['labelToId'] = self.label_to_id
        ret['labelToColor'] = self.label_to_color
        if self.min_width: ret['minWidth'] = self.min_width
        if self.max_width: ret['maxWidth'] = self.max_width
        if self.min_height: ret['minHeight'] = self.min_height
        if self.max_height: ret['maxHeight'] = self.max_height
        if self.width: ret['width'] = self.width
        if self.height: ret['height'] = self.height
        return ret
