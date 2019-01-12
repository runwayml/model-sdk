#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='runway-python',
    version='0.0.3',
    description='Helper library for creating Runway models',
    author='Anastasis Germanidis',
    author_email='anastasis@runwayml.com',
    url='https://github.com/runwayml/python-sdk',
    packages=['runway'],
    scripts=[],
    install_requires=[
        'Flask>=0.12.2',
        'Flask-Cors>=3.0.2',
        'numpy>=1.15.1',
        'Pillow>=4.3.0'
    ],
    license="MIT"
)
