import sys
import base64
if sys.version_info[0] < 3:
    from cStringIO import StringIO as IO
else:
    from io import BytesIO as IO
import numpy as np
from PIL import Image
from .utils import is_url, download_to_temp_dir


def try_cast_np_scalar(value):
    if type(value).__module__ == 'numpy' and np.isscalar(value):
        return value.item()
    return value


def deserialize_image(value):
    image = value[value.find(",")+1:]
    image = base64.decodestring(image.encode('utf8'))
    buffer = IO(image)
    return Image.open(buffer)


def serialize_image(value):
    if type(value) is np.ndarray:
        im_pil = Image.fromarray(value)
    elif type(value) is Image.Image:
        im_pil = value
    buffer = IO()
    im_pil.save(buffer, format='JPEG')
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('utf8')


def deserialize(value, arg_type):
    if arg_type == 'text':
        return value
    elif arg_type == 'image':
        return deserialize_image(value)
    elif arg_type == 'float':
        return float(try_cast_np_scalar(value))
    elif arg_type == 'integer':
        return int(try_cast_np_scalar(value))
    elif arg_type == 'vector':
        return np.array(value)
    elif arg_type == 'checkpoint':
        if is_url(value):
            return download_to_temp_dir(value)
    return value


def serialize(value, arg_type):
    if arg_type == 'text':
        return str(value)
    elif arg_type == 'image':
        return serialize_image(value)
    elif arg_type == 'integer':
        return int(value)
    elif arg_type == 'float':
        return float(value)
    elif arg_type == 'vector':
        return value.tolist()
    elif type(arg_type) == list:
        ret = []
        for output in value:
            serialized_output = {}
            for output_name, output_value in output.items():
                serialized_output[output_name] = serialize(
                    output_value, arg_type[0][output_name])
            ret.append(serialized_output)
        return ret
    return value