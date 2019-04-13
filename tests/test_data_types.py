# Ensure that the local version of the runway module is used, not a pip
# installed version
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')

import pytest
from runway.data_types import *
from runway.exceptions import *

# UTIL FUNCTIONS ---------------------------------------------------------------
def check_data_type_interface(data_type):
    assert callable(data_type.serialize)
    assert callable(data_type.deserialize)
    assert callable(data_type.to_dict)

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

def test_array_deserialization():
    expect = ['10', '100', '1000']
    assert expect == array(item_type=text).deserialize(['10', '100', '1000'])
