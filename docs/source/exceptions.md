# Exceptions

The Runway Model SDK defines several custom exception types. All of these exceptions derive from the base ``RunwayError`` class, which itself derives from the standard Python ``Exception`` class. Each ``RunwayException`` contain error `message` and `code` properties, and a `to_response()` method that converts the exception to a Python dictionary, which can be returned as a JSON HTTP response.

```python
try:
    do_something_with_runway()
except RunwayError as e:
    print(e.code, e.message)
    # 500 An unknown error has occurred
    print(e.to_response())
    # { "error": "An unknown error has occurred", "traceback": "..." }
```

## Reference

```eval_rst
.. automodule:: runway.exceptions
    :members:
    :inherited-members:
    :member-order: bysource
    :exclude-members: with_traceback
    :show-inheritance:
```