#!/usr/bin/env python

version="1.0"
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


here = os.path.abspath(os.path.dirname(__file__))

# Fix the encoding issue by explicitly specifying UTF-8
try:
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        README = f.read()
except UnicodeDecodeError:
    # Fallback in case README.md has encoding issues
    README = "PySInfo: A python command line tool that displays system information"

setup(name='pysinfo',
      version=version,
      description='PySInfo: A python command line tool that displays information about the current system, including hardware and critical software.',
      long_description=README,
      long_description_content_type='text/markdown',
      author='cycleuser',
      author_email='cycleuser@cycleuser.org',
      url='http://blog.cycleuser.org',
      packages=['pysinfo'],
      install_requires=[ 
                        "psutil",
                        "distro",
                        "GPUtil",
                        "colorama"
                         ],
     )