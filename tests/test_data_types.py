# Ensure that the local version of the runway module is used, not a pip
# installed version
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')

import os
import pytest
import numpy as np
from PIL import Image
from runway.data_types import *
from runway.exceptions import *

# UTIL FUNCTIONS ---------------------------------------------------------------
def check_data_type_interface(data_type):
    assert callable(data_type.serialize)
    assert callable(data_type.deserialize)
    assert callable(data_type.to_dict)

# We arbitrarily use this release tag to test file download and serialization
def check_expected_contents_for_0057_tar_download(path):
    readme_path = os.path.join(path, 'model-sdk-0.0.57', 'README.md')
    assert os.path.isfile(readme_path)
    with open(readme_path, 'r') as f:
        assert f.read() == '# Runway Python SDK\n'

# BASIC TESTS FOR ALL DATA TYPES -----------------------------------------------
def test_data_type_interface_any():
    check_data_type_interface(any)

def test_data_type_interface_array():
    check_data_type_interface(array)

def test_data_type_interface_image():
    check_data_type_interface(image)

def test_data_type_interface_vector():
    check_data_type_interface(vector)

def test_data_type_interface_category():
    check_data_type_interface(category)

def test_data_type_interface_number():
    check_data_type_interface(number)

def test_data_type_interface_text():
    check_data_type_interface(text)

def test_data_type_interface_file():
    check_data_type_interface(file)

# TEXT -------------------------------------------------------------------------
def test_text_to_dict():
    default = 'Some default text'
    txt = text(default=default, min_length=1, max_length=20)
    obj = txt.to_dict()
    assert obj['type'] == 'text'
    assert obj['name'] == 'text'
    assert obj['default'] == default
    assert obj['minLength'] == 1
    assert obj['maxLength'] == 20

def test_text_serialization():
    txt = text()
    assert txt.serialize(512) == '512'

def test_text_deserialize():
    txt = text()
    assert txt.deserialize('512') == '512'

# NUMBER -----------------------------------------------------------------------
def test_number_to_dict():
    default = 42
    num = number(default=default, min=10, max=100)
    obj = num.to_dict()
    assert obj['type'] == 'number'
    assert obj['name'] == 'number'
    assert obj['default'] == default
    assert obj['min'] == 10
    assert obj['max'] == 100
    assert obj['step'] == 1

def test_number_serialization():
    assert 1 == number().serialize(1)
    assert 1.1 == number().serialize(1.1)

def test_number_deserialize():
    assert 1 == number().deserialize(1)
    assert 1.1 == number().deserialize(1.1)

def test_number_deserialize_numpy_scalar():
    assert 10 == number().deserialize(np.float(10))

def test_number_serialize_numpy_scalar():
    assert 10 == number().serialize(np.float(10))

# ARRAY ------------------------------------------------------------------------
def test_array_to_dict():
    arr = array(item_type=text, min_length=5, max_length=10)
    obj = arr.to_dict()
    assert obj['name'] == 'text_array'
    assert obj['type'] == 'array'
    assert obj['itemType'] == text().to_dict()
    assert obj['minLength'] == 5
    assert obj['maxLength'] == 10

def test_array_no_item_type():
    with pytest.raises(MissingArgumentError):
        arr = array()

def test_array_serialization():
    expect = ['10', '100', '1000']
    assert expect == array(item_type=text).serialize([10, 100, 1000])

    expect = ['one', 'two', 'three']
    assert expect == array(item_type=text).serialize(['one', 'two', 'three'])

    expect = [10, 100, 1000]
    arr = array(item_type=vector(length=3))
    assert expect == arr.serialize(np.array(expect))

def test_array_deserialization():
    expect = ['one', 'two', 'three']
    assert expect == array(item_type=text).deserialize(['one', 'two', 'three'])

    expect = np.array([10, 100, 1000])
    arr = array(item_type=vector(length=3))
    assert np.array_equal(expect, arr.deserialize(expect.tolist()))

# VECTOR -----------------------------------------------------------------------
def test_vector_to_dict():
    vec = vector(length=128, sampling_mean=0, sampling_std=1)
    obj = vec.to_dict()
    assert obj['name'] == 'vector'
    assert obj['type'] == 'vector'
    assert obj['length'] == 128
    assert obj['samplingMean'] == 0
    assert obj['samplingStd'] == 1

def test_vector_no_item_type():
    with pytest.raises(MissingArgumentError):
        vec = vector()

def test_vector_serialization():
    zeros = np.zeros(128)
    serialized = vector(length=128).serialize(zeros)
    assert np.array_equal(np.array(zeros), serialized)
    assert type(serialized) == list

def test_vector_deserialization():
    zeros = np.zeros(128)
    deserialized = vector(length=128).deserialize(zeros)
    assert np.array_equal(zeros.tolist(), deserialized)
    assert isinstance(deserialized, np.ndarray)

# CATEGORY ---------------------------------------------------------------------
def test_category_to_dict():
    cat = category(choices=['one', 'two', 'three'], default='two')
    obj = cat.to_dict()
    assert obj['name'] == 'category'
    assert obj['type'] == 'category'
    assert obj['oneOf'] == ['one', 'two', 'three']
    assert obj['default'] == 'two'

def test_category_serialization():
    cat = category(choices=['one', 'two', 'three'], default='two')
    assert 'one' == cat.serialize('one')

def test_category_deserialization():
    cat = category(choices=['one', 'two', 'three'], default='two')
    assert 'one' == cat.deserialize('one')

def test_category_choices_none():
    with pytest.raises(MissingArgumentError):
        cat = category()

def test_category_choices_empty_arr():
    with pytest.raises(MissingArgumentError):
        cat = category(choices=[])

def test_category_default_not_in_choices():
    with pytest.raises(InvalidArgumentError):
        cat = category(choices=['one', 'two'], default='three')

def test_category_default_choice():
    cat = category(choices=['one', 'two', 'three'], default='two')
    assert cat.default == 'two'

def test_category_default_choice_is_first_if_not_specified():
    cat = category(choices=['one', 'two', 'three'])
    assert cat.default == 'one'

def test_category_deserialized_value_is_not_in_choices():
    cat = category(choices=['one', 'two', 'three'])
    with pytest.raises(InvalidArgumentError):
        cat.deserialize('four')

# FILE -------------------------------------------------------------------------
def test_file_to_dict():
    f = file()
    obj = f.to_dict()
    assert obj['name'] == 'file'
    assert obj['type'] == 'file'

def test_file_to_dict_folder():
    f = file(is_folder=True)
    obj = f.to_dict()
    assert obj['name'] == 'file'
    assert obj['type'] == 'file'
    assert obj['isFolder'] == True

def test_file_serialization_base():
    f = file()
    assert 'file.txt' == f.serialize('file.txt')

def test_file_serialization_relative():
    f = file()
    assert 'folder/file.txt' == f.serialize('folder/file.txt')

def test_file_serialization_absolute():
    f = file()
    assert '/home/user/file.txt' == f.serialize('/home/user/file.txt')

def test_file_serialization_remote():
    f = file()
    url = 'https://github.com/runwayml/model-sdk/archive/0.0.57.tar.gz'
    assert url == f.serialize(url)
## TODO: accept ftp:// protocol
#     url = 'ftp://demo:password@test.rebex.net/readme.txt'
#     assert url == f.serialize(url)

def test_file_serialization_base_folder():
    f = file(is_folder=True)
    assert 'folder' == f.serialize('folder')

def test_file_serialization_relative_folder():
    f = file(is_folder=True)
    assert 'folder/folder' == f.serialize('folder/folder')

def test_file_serialization_absolute_folder():
    f = file(is_folder=True)
    assert '/home/user/folder' == f.serialize('/home/user/folder')

def test_file_serialization_remote_folder():
    f = file(is_folder=True)
    url = 'https://github.com/runwayml/model-sdk/archive/0.0.57.tar.gz'
    assert url == f.serialize(url)
## TODO: accept ftp:// protocol
#     url = 'ftp://demo:password@test.rebex.net/'
#     assert url == f.serialize(url)

def test_file_deserialization_base():
    f = file()
    assert 'file.txt' == f.deserialize('file.txt')

def test_file_deserialization_relative():
    f = file()
    assert 'folder/file.txt' == f.deserialize('folder/file.txt')

def test_file_deserialization_absolute():
    f = file()
    assert '/home/user/file.txt' == f.deserialize('/home/user/file.txt')

def test_file_deserialization_remote():
    f = file()
    url = 'https://github.com/runwayml/model-sdk/archive/0.0.57.tar.gz'
    path = f.deserialize(url)
    assert os.path.exists(path)
    check_expected_contents_for_0057_tar_download(path)

def test_file_deserialization_base_folder():
    f = file(is_folder=True)
    assert 'folder' == f.deserialize('folder')

def test_file_deserialization_relative_folder():
    f = file(is_folder=True)
    assert 'folder/folder' == f.deserialize('folder/folder')

def test_file_deserialization_absolute_folder():
    f = file(is_folder=True)
    assert '/home/user/folder' == f.deserialize('/home/user/folder')

def test_file_deserialization_remote_folder():
    f = file(is_folder=True)
    url = 'https://github.com/runwayml/model-sdk/archive/0.0.57.tar.gz'
    path = f.deserialize(url)
    assert os.path.exists(path)
    check_expected_contents_for_0057_tar_download(path)

# IMAGE ------------------------------------------------------------------------
def test_image_to_dict():
    img = image(channels=3, min_width=128, min_height=128, max_width=512, max_height=512)
    obj = img.to_dict()
    assert obj['type'] == 'image'
    assert obj['name'] == 'image'
    assert obj['channels'] == 3
    assert obj['minWidth'] == 128
    assert obj['maxWidth'] == 512
    assert obj['minHeight'] == 128
    assert obj['maxHeight'] == 512

def test_image_serialize_and_deserialize():
    folder = os.path.dirname(os.path.realpath(__file__))
    img = Image.open(os.path.join(folder, 'test_image.jpg'))
    serialized_pil = image().serialize(img)
    deserialized_pil = image().deserialize(serialized_pil)
    assert issubclass(type(deserialized_pil), Image.Image)

    serialize_np_img = image().serialize(np.asarray(img))
    deserialize_np_img = image().deserialize(serialize_np_img)
    assert issubclass(type(deserialize_np_img), Image.Image)

def test_image_serialize_invalid_type():
    with pytest.raises(InvalidArgumentError):
        image().serialize(True)

    with pytest.raises(InvalidArgumentError):
        image().serialize([])

    with pytest.raises(InvalidArgumentError):
        image().serialize('data:image/jpeg;base64,')