<a href="#" target='_self' >
  <p align="center">
    <img src="assets/banner.png">
  </p>
</a>


[![CircleCI branch](https://img.shields.io/circleci/project/github/runwayml/model-sdk/master.svg)](https://circleci.com/gh/runwayml/model-sdk/tree/master)
[![docs](https://readthedocs.org/projects/runway-model-sdk/badge/?version=latest&style=flat)](https://sdk.runwayml.com)
[![codecov](https://codecov.io/gh/runwayml/model-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/runwayml/model-sdk)
<a href="https://runwayml.com/joinslack"><img src="https://img.shields.io/badge/slack-runwayml.slack.com-33b279.svg"></a>

The Runway Model SDK allows you to port new and existing machine learning models to the Runway platform. With a few lines of code, you can modify your Python model to be used and shared by others on [Runway](https://runwayml.com).

## Installing

The SDK supports both Python 2.7 and Python 3, but we recommend using Python 3. You can install the module using either pip or pip3 like so:

```
pip3 install runway-python
```

Now head over to [the sdk docs](https://sdk.runwayml.com) to learn how to use the Runway Model SDK.

## Docs

Reference and documentation for the Runway Model SDK is hosted at [sdk.runwayml.com](https://sdk.runwayml.com). These docs provide an overview of how to use the SDK to port your own ML models.

The [Runway Model Template repo](https://github.com/runwayml/model-template) also contains a simple example of how to get started porting a model to Runway.

See the *Importing Models into Runway* [tutorial](https://docs.runwayapp.ai/#/importing) for a walk-through illustrating how to port a model to Runway.

## Developing

If you'd like to contribute to the development of the Runway Python SDK, you can clone and modify this repository by following the instructions below. At the time of this writing the SDK is compatible with Python 2.7 and Python 3, however our developer dependencies `requirements-dev.txt` require Python 3.

```bash
git clone https://github.com/runwayml/model-sdk runway-model-sdk
cd runway-model-sdk

## optionally use a virtual environment
# virtualenv -p python3 venv && source venv/bin/activate

# install dependencies
python3 setup.py install

# install the dev dependencies
make dev
```

### Testing

Automated tests for the Runway Model SDK are written using `pytest` and live in the `tests/` directory. We also provide support for code coverage via `pytest-cov`. Tests can be run in both Python 2.7 or Python 3 environments.

```bash
## Create and activate a python3 virtual environment if you need to.
# virtualenv -p python3 venv && source ./venv/bin/activate

# make sure you have the development dependencies installed
make dev

# run the tests
make test

# by default pytest suppresses stdout and stderr during testing, so run tests
# like this if you'd like to see the output from your print() statements during
# testing
make test-debug

# to generate coverage statistics while running tests, use this command.
# it prints test coverage to the console and also generates a more detailed HTML
# report in htmlcov/.
make coverage
```

If you make a PR against this repo, please be sure to include automated tests to validate that your code works as expected. PRs will be automatically blocked by a [Codecov](https://codecov.io/) bot if their changes reduce the overall test coverage of the Runway Model SDK package.

### Building the Docs

The Model SDK documentation is generated from inline source code using docstrings,  [Sphinx](http://www.sphinx-doc.org/en/master/), and a modified Read the Docs HTML theme. The version of Sphinx that we are using (v2.0.1) requires Python 3.

```bash
## Create and activate a python3 virtual environment if you need to.
# virtualenv -p python3 venv && source ./venv/bin/activate

# make sure you have the docs dependencies installed
make dev-docs

# build the docs
make docs
```

Your auto-generated HTML docs should now appear in `docs/build/html`.

### Questions

We have a `#model-sdk` channel in our public [Slack](https://runwayml.com/joinslack) workspace that you can use to ask questions or chat with the Runway team about this Python module. Feel free to open an issue as well!
