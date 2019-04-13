# Runway Model SDK

[![CircleCI branch](https://img.shields.io/circleci/project/github/runwayml/model-sdk/master.svg)](https://circleci.com/gh/runwayml/model-sdk/tree/master)
[![docs](https://readthedocs.org/projects/runway-model-sdk/badge/?version=latest&style=flat)](https://sdk.runwayml.com)
[![codecov](https://codecov.io/gh/runwayml/model-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/runwayml/model-sdk)
[![Runway Slack](https://img.shields.io/badge/slack-runwayml.slack.com-33b279.svg)](https://runwayml.slack.com/)

The Runway Model SDK allows you to port new and existing machine learning models to the Runway platform. With a few lines of code, you can modify your Python model to be used and shared by others on [Runway](https://runwayml.com).

<!--
The model template repo is currently private, but we'll add this text when it become public:

Take a look at the [Runway Model Template repo](https://github.com/runwayml/model-template), which contains a simple example of how to get started porting a model to Runway.
-->

## Installing

The SDK supports both Python 2.7 and Python 3, but we recommend using Python 3. You can install the module using either pip or pip3 like so:

```
pip3 install runway-python
```

Now head over to [the docs](https://sdk.runwayml.com) to learn how to use the Runway Model SDK.

## Docs

Reference and documentation for the Runway Model SDK is hosted at [sdk.runwayml.com](https://sdk.runwayml.com). These docs provide an overview of how to use the SDK to port your own ML models.

> Note: We are currently configuring sdk.runwayml.com, so the publicly hosted version of the docs may be unavailable. You can always [build the docs yourself](#building-the-docs) in the meantime.

## Developing

If you'd like to contribute to the development of the Runway Python SDK, you can clone and modify this repository by following the instructions below. At the time of this writing the SDK is compatible with Python 2.7 and Python 3, however we strongly recommend that you use this SDK with Python 3.

```bash
git clone https://github.com/runwayml/model-sdk runway-model-sdk
cd runway-model-sdk

## optionally use a virtual environment
# virtualenv -p python3 venv
# source venv/bin/activate

# install dependencies
python3 setup.py install

# install the dev dependencies
make dev
```

### Building the Docs

The Model SDK documentation is generated from inline source code using docstrings,  [Sphinx](http://www.sphinx-doc.org/en/master/), and a modified Read the Docs HTML theme.

```bash
# make sure you have the dev dependencies installed
make dev

# build the docs
make docs
```

Your autogenerated HTML docs should now appear in `docs/build/html`.

