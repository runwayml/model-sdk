import tempfile
import tarfile
import re
import wget
import os


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
