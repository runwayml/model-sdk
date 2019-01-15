import base64
import io
import numpy as np
from PIL import Image


def deserialize_image(value):
    image = value[value.find(",")+1:]
    image = base64.decodestring(image.encode('utf8'))
    return Image.open(io.BytesIO(image))


def serialize_image(value):
    if type(value) is np.ndarray:
        im_pil = Image.fromarray(value)
    elif type(value) is Image.Image:
        im_pil = value
    buffer = io.BytesIO()
    im_pil.save(buffer, format='JPEG')
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('utf8')


def deserialize(value, arg_type):
    if arg_type == 'text':
        return value
    elif arg_type == 'image':
        return deserialize_image(value)
    elif arg_type == 'float':
        return float(value)
    elif arg_type == 'integer':
        return int(value)
    elif arg_type == 'vector':
        return np.array(value)
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