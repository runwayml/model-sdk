import tempfile
import tarfile
import inspect
import re
import wget
import os
import functools
import sys
import gzip
if sys.version_info[0] < 3:
    from cStringIO import StringIO as IO
else:
    from io import BytesIO as IO
import numpy as np
from flask import after_this_request, request
import colorsys


URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def serialize_command(cmd):
    ret = {}
    ret['name'] = cmd['name']
    ret['inputs'] = [inp.to_dict() for inp in cmd['inputs']]
    ret['outputs'] = [inp.to_dict() for inp in cmd['outputs']]
    return ret


def is_url(path):
    return re.match(URL_REGEX, path)


def download_to_temp_dir(url):
    print('Downloading file: %s' % url)
    tmp_path = tempfile.mkdtemp()
    fname = wget.download(url)
    tar = tarfile.open(fname, "r:gz")
    tar.extractall(path=tmp_path)
    tar.close()
    os.remove(fname)
    return tmp_path


def gzip_decompress(data):
    compressed_data = IO(data)
    return gzip.GzipFile(fileobj=compressed_data, mode='r').read()


def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response

            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func


def try_cast_np_scalar(value):
    if type(value).__module__ == 'numpy' and np.isscalar(value):
        return value.item()
    return value


def cast_to_obj(cls_or_obj):
    if inspect.isclass(cls_or_obj):
        return cls_or_obj()
    return cls_or_obj


# Generate random colormap, adapted from https://github.com/delestro/rand_cmap/blob/master/rand_cmap.py
def random_color_map(n_labels):
    hsv_colors = [(np.random.uniform(low=0.0, high=1),
                   np.random.uniform(low=0.2, high=1),
                   np.random.uniform(low=0.9, high=1)) for i in range(n_labels)]
    rgb_colors = []
    for hsv_color in hsv_colors:
        rgb_colors.append(colorsys.hsv_to_rgb(hsv_color[0], hsv_color[1], hsv_color[2]))
    rgb_colors[0] = [0, 0, 0]
    return [[round(r*255), round(g*255), round(b*255)] for r, g, b in rgb_colors]
