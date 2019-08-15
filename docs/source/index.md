# Runway Model SDK

These documents serve as a reference for the [Runway](https://runwayml.com) Model SDK. With a few lines of code, you can port existing ML models to the Runway platform so they can be used and shared by others.

## Installing

This SDK supports both Python 2.7 and Python 3, but we recommend using Python 3. You can install the module using either `pip` or `pip3` like so:

```bash
pip3 install runway-python
```

Published versions of the SDK are hosted on the [PyPI project website](https://pypi.org/project/runway-python/).

## Runway Models

A Runway model consists of two special files:

- `runway_model.py`: A python script that imports the [`runway` module](runway_module.html) (SDK) and exposes its interface via one or more `runway.command()` functions. This file is used as the **entrypoint** to your model.
- [`runway.yml`](runway_yaml_file.html): A configuration file that describes dependencies and build steps needed to build and run the model.

### Example `runway_model.py`

Runway models expose a standard interface that allows the Runway app to interact with them over HTTP. This is accomplished using three functions: `@runway.setup()`, `@runway.command()`, and `runway.run()`.

Any Python-based model, independent of the ML framework or toolkit, can be converted into a Runway model using this simple interface. For more information about the `runway` module, see the [module reference](runway_module.html) page.

```eval_rst
.. note::
    This is example code for demonstration purposes only. It will not
    run, as the ``your_image_generation_model`` import is not a real python
    module.
```

```python
import runway
from runway.data_types import category, vector, image
from your_image_generation_model import big_model, little_model

# The setup() function runs once when the model is initialized, and will run
# again for each well formed HTTP POST request to http://localhost:9000/setup.
@runway.setup(options={'model_size': category(choices=['big', 'little'])})
def setup(opts):
    if opts['model_size'] == 'big':
        return big_model()
    else:
        return little_model()

inputs = { 'noise_vector': vector(length=128, description='A random seed.') }
outputs = { 'image': image(width=512, height=512) }

# The @runway.command() decorator is used to create interfaces to call functions
# remotely via an HTTP endpoint. This lets you send data to, or get data from,
# your model. Each command creates an HTTP route that the Runway app will use
# to communicate with your model (e.g. POST /generate). Multiple commands
# can be defined for the same model.
@runway.command('generate', inputs=inputs, outputs=outputs, description='Generate an image.')
def generate(model, input_args):
    # Functions wrapped by @runway.command() receive two arguments:
    # 1. Whatever is returned by a function wrapped by @runway.setup(),
    #    usually a model.
    # 2. The input arguments sent by the remote caller via HTTP. These values
    #    match the schema defined by inputs.
    img = input_args['image']
    return model.generate(img)

# The runway.run() function triggers a call to the function wrapped by
# @runway.setup() passing model_options as its single argument. It also
# creates an HTTP server that listens for and fulfills remote requests that
# trigger commands.
if __name__ == '__main__':
    runway.run(host='0.0.0.0', port=9000, model_options={ 'model_size': 'big' })
```

If you are looking to port your own model, we recommend starting from our [Model Template](https://github.com/runwayml/model-template) repository hosted on GitHub. This repository contains a basic model that you can use as boilerplate instead of having to start from scratch.

### Example `runway.yml`

Each Runway model must have a `runway.yml` configuration file in its root directory. This file defines the steps needed to build and run your model for use with the Runway app. This file is written in YAML, a human-readable superset of JSON. Below is an example `runway.yml` file. This example file illustrates how you can provision your model's environment.

```yaml
version: 0.1
python: 3.6
entrypoint: python runway_model.py
cuda: 9.2
framework: tensorflow
files:
    ignore:
        - image_dataset/*
build_steps:
    - pip install runway-python
    - pip install -r requirements.txt
```

Continue on to the [Runway YAML reference page](runway_yaml_file.html) to learn more about the possible configuration values supported by the `runway.yml` file, or hop over to the [Example Models](example_models.html) page to check out the source code for some of the models that have already been ported to Runway.

<!-- http://www.sphinx-doc.org/en/1.5/markup/toctree.html -->
```eval_rst
.. toctree::
    :maxdepth: 2
    :name: mastertoc
    :hidden:

    Home <index>
    Runway YAML File <runway_yaml_file>
    Runway Module <runway_module>
    Data Types <data_types>
    Exceptions <exceptions>
    UI Components <ui_components>
    Example Models <example_models>
    CHANGELOG <https://github.com/runwayml/model-sdk/blob/master/CHANGELOG.md>
```
