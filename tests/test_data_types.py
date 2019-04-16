# Ensure that the local version of the runway module is used, not a pip
# installed version
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')

import pytest
import numpy as np
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
