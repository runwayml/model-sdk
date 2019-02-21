#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='runway-python',
    version='0.0.43',
    description='Helper library for creating Runway models',
    author='Anastasis Germanidis',
    author_email='anastasis@runwayml.com',
    url='https://github.com/runwayml/python-sdk',
    packages=['runway'],
    scripts=[],
    install_requires=[
        'Flask>=0.12.2',
        'Flask-Cors>=3.0.2',
        'numpy>=1.15.0',
        'Pillow>=4.3.0',
        'gevent>=1.4.0',
        'wget>=3.2'
    ],
    license="MIT"
)
