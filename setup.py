#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup
    from distutils.cmd import Command

here = os.path.abspath(os.path.dirname(__file__))

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.md') as f:
    long_description = f.read()

about = {}
with open(os.path.join(here, 'runway', '__version__.py'), 'r') as f:
    exec(f.read(), about)

class VerifyVersionCommand(Command):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != about['__version__']:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, about['__version__']
            )
            sys.exit(info)

class TagReleaseCommand(Command):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('git tag %s' % about['__version__'])

setup(
    name='runway-python',
    version=about['__version__'],
    description='Helper library for creating Runway models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Runway AI, Inc.',
    author_email='support@runwayml.com',
    url='https://github.com/runwayml/model-sdk',
    packages=['runway'],
    scripts=[],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    install_requires=requirements,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"        
    ],
    cmdclass={
        'verify': VerifyVersionCommand,
        'tag_release': TagReleaseCommand
    }
)
