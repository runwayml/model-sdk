# Runway Python SDK

These documents serve as a reference for the [Runway](https://runwayml.com) Python SDK. With a few lines of code, you can port an existing ML model to the Runway platform so that it can be used and shared by others.

## Installing

This SDK supports both Python 2.7 and Python 3, but we recommend using Python 3. You can install the module using either `pip` or `pip3` like so:

```bash
pip3 install runway-python
```

Published versions of the SDK are hosted on the [PyPI project website](https://pypi.org/project/runway-python/).

## Example Model

A Runway model consists of two special files:

- `runway_model.py`: A python script that imports the `runway` module (SDK) and exposes its interface via `runway.commands()`. This file is used as the **entrypoint** to your model.
- `runway.yml`: A spec file that describes dependencies and build steps needed to build and run the model.

If you are looking to port your own model, we recommend starting from our [Model Template](https://github.com/runwayml/model-template) repository hosted on GitHub. This repository contains a basic model that you can use as boilerplate instead of having to start from scratch.

## Contents

<!-- http://www.sphinx-doc.org/en/1.5/markup/toctree.html -->
```eval_rst
.. toctree::
    :maxdepth: 2
    :name: mastertoc

    Runway Module <runway_module>
    Runway YAML Spec File <runway_spec_file>
    Data Types <data_types>
    Exceptions <exceptions>
```