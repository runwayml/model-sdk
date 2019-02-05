import tempfile
import tarfile
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
from flask import after_this_request, request


URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def to_long_spec(spec):
    long_spec = []
    for key, value in spec.items():
        if type(value) == str:
            value = {'name': key, 'type': value}
        elif type(value) == list:
            value = {'name': key, 'type': {'arrayOf': to_long_spec(value[0])}}
        elif type(value) == dict:
            value = {'name': key, 'type': to_long_spec(value)}
        long_spec.append(value)
    return long_spec


def is_url(path):
    return re.match(URL_REGEX, path)


def download_to_temp_dir(url):
    print('Downloading checkpoint: %s' % url)
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
