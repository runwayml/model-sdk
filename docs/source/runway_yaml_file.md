# Runway YAML File

A `runway.yml` file is required to be in the root file directory of each Runway model. This file provides instructions for defining an environment, installing dependencies, and running your model in a standard and reproducible manner. These instructions are used by the Runway build pipeline to create a Docker image that can be run in a platform independent way on a local machine or a remote cloud GPU instance (although this process is abstracted away from the model builder). The `runway.yml` config file is written in [YAML](https://learnxinyminutes.com/docs/yaml/) and has a simple structure. You are free to copy and paste the example config file below, changing or removing the values that you need.

```eval_rst
.. note::
    The Runway configuration file must be named ``runway.yml`` and exist in the root (top-level) directory of your model.
```

## Example

```yaml
# Specify the version of the runway.yml spec.
version: 1
# Supported python versions are 2.7, 3.6, and 3.7
python: 3.7
# The command to run your model. This value is used as the CMD value in
# the generated Docker image.
entrypoint: python runway_model.py
# Which NVIDIA CUDA version to use. Supported versions include 10, 9.2, and 9.
cuda: 9.2
# Which ML framework would you like to pre-install? The appropriate GPU/CPU
# versions of these libraries are selected automatically. Accepts values
# "tensorflow" and "pytorch", installinv Tensorflow v1.12 and Pytorch v1.0
# respectively.
framework: tensorflow
# Builds are created for CPU and GPU environments by default. You can use the
# spec object to limit your builds to one environment if you'd like, for
# instance if your model doesn't use CUDA or run on a GPU you can set
# gpu: False.
spec:
    cpu: True
    gpu: True
files:
    # All files in the root project directory will be copied to the Docker image
    # automatically. Builds that require excessive storage can fail or take a
    # very long time to install on another user's machine. You can use the
    # files.ignore array to exclude files from your build.
    ignore:
        - my_dataset/*
        - secrets.txt
# The build_steps array allows you to run shell commands during . Each build
# step is translated to a Docker RUN command, and commands are run in the order
# they appear in the array.
build_steps:
    # We recommend pinning to a version of the Runway Model SDK until the first
    # major release as breaking changes may be introduced to the SDK
    - pip install runway-python==0.1.0
    - pip install -r requirements.txt
    # The if_gpu and if_cpu directives can be used to run build steps
    # conditionally depending on the build environment.
    - if_gpu: echo "Building in a GPU environment..."
    - if_cpu: echo "Building in a CPU only environment..."
```

```eval_rst
.. note::
    If you require an ML framework other than Tensorflow or Pytorch, or a version of these libraries that is different than the versions provided by the ``frameworks`` object, you can install these dependencies manually in the build steps.

    .. code-block:: yaml

        build_steps:
            - pip install tensorflow==1.0
            - if_gpu: pip install tensorflow-gpu==1.0
```

## Schema Reference

- `version` (int, optional, default = `1`): This version specifies the schema of the configuration file not the version of the Runway Model SDK itself.
- `python` (float, **required**): The Python version to use when running the model installing python dependencies.
- `entrypoint` (string, **required**): The command to run your model. This value is used as the CMD value in the generated Docker image. A standard value for this field might be `entrypoint: python runway_model.py` where `runway_model.py` implements the `@runway.setup()`, `@runway.command()`, and most importantly the `runway.run()` functions.
- `cuda` (float, **required if building for GPU**): The NVIDIA CUDA version to use in the production GPU runtime environment. The currently supported CUDA versions are `10`, `9.2`, and `9`.
- `framework` (string, optional, default = `None`): The machine learning framework to pre-install during the build. Currently we support `"tensorflow"` and `"pytorch"` which will install the appropriate CPU or GPU packages of Tensorflow v1.12.0 and Pytorch v1.0 respectively depending on the build environment. If you require an ML framework other than Tensorflow or Pytorch, or a version of these libraries that is different than the versions provided by the ``frameworks`` object, you can omit this object and install these dependencies manually in the build steps.
- `spec` (object, optional): A dictionary of boolean values specifying which CPU/GPU environments to build for. Both the `cpu` and `gpu` environments are enabled (`True`) by default.
    - `cpu` (boolean, optional, default = `True`): Create a CPU build.
    - `gpu` (boolean, optional, default = `True`): Create a GPU build.
- `files` (object, optional): A dictionary that defines special behaviors for certain files. All values in this dictionary are specified as paths, with support for the glob character (e.g. `data/*.jpg`).
    - `ignore` (array of strings, optional): A list of file paths to exclude from the build.
- `build_steps` (array of strings or dictionary values containing the `if_cpu` and `if_gpu` keys, optional): A list of shell commands to run at build time. Use this list to define custom build steps. Each build step is translated to a Docker RUN command, and commands are run in the order they appear in the array.
