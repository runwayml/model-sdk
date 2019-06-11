import tempfile
import tarfile
import inspect
import re
import wget
import os
import functools
import sys
import gzip
import datetime
import colorcet
if sys.version_info[0] < 3:
    from cStringIO import StringIO as IO
else:
    from io import BytesIO as IO
import numpy as np
from flask import after_this_request, request, jsonify


URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def validate_post_request_body_is_json(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        json = get_json_or_none_if_invalid(request)
        if json is not None:
            return f(*args, **kwargs)
        else:
            err_msg = 'The body of all POST requests must contain JSON'
            return jsonify(dict(error=err_msg)), 400
    return wrapped

def get_json_or_none_if_invalid(request):
    return request.get_json(force=True, silent=True)

def serialize_command(cmd):
    ret = {}
    ret['name'] = cmd['name']
    ret['description'] = cmd['description']
    ret['inputs'] = [inp.to_dict() for inp in cmd['inputs']]
    ret['outputs'] = [inp.to_dict() for inp in cmd['outputs']]
    return ret


def is_url(path):
    return re.match(URL_REGEX, path)


def download_file(url):
    download_dir = tempfile.mkdtemp()
    return wget.download(url, out=download_dir)


def extract_tarball(path):
    extracted_dir = tempfile.mkdtemp()
    with tarfile.open(path, 'r:*') as tar:
        tar.extractall(path=extracted_dir)
    return extracted_dir


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


def timestamp_millis():
    offset = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    return int(offset.total_seconds() * 1000)


def get_color_palette(name):
    palette = getattr(colorcet, name)
    return [[int(c[0]*255), int(c[1]*255), int(c[2]*255)] for c in palette]

  
def argspec(fn):
    if sys.version_info[0] < 3:
        return inspect.getargspec(fn)
    else:
        return inspect.getfullargspec(fn)
