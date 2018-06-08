#!/usr/bin/python

from setuptools import setup
import sys

from iati2hxl import __version__

if sys.version_info < (3,):
    raise RuntimeError("iati2hxl requires Python 3 or higher")

setup(name='iati2hxl',
      version=__version__,
      description='Convert IATI to HXL',
      author='David Megginson',
      author_email='contact@megginson.com',
      install_requires=['requests'],
      packages=['iati2hxl'],
)
