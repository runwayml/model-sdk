# Runway Module

The runway module exposes three simple functions that can be combined to expose your models to the Runway app using a simple interface.

- [`@runway.setup()`](#runway.setup): A decorator used to initialize and configure your model.
- [`@runway.command()`](#runway.command): A decorator used to define the interface to your model. Each command creates an HTTP route which can process user input and return outputs from the model.
- [`runway.run()`](#runway.run): The entrypoint function that starts the SDK's HTTP interface. It fires the function decorated by `@runway.setup()` and listens for commands on the network, forwarding them along to the appropriate functions decorated with `@runway.command()`.

## Reference
<!--
Because the runway/__init__.py file defines its functions via assignment from runway/model.py, we have to use this autofunction trick to make sure the function signatures show up correctly.
See https://stackoverflow.com/questions/5365684/is-it-possible-to-override-sphinx-autodoc-for-specific-functions/5368194#5368194
-->
```eval_rst
.. automodule:: runway

.. autofunction:: setup(decorated_fn=None, options=None)
.. autofunction:: command(name, inputs={}, outputs={})
.. autofunction:: run()
```