#!/usr/bin/env python

version="1.0"
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


here = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(here, 'README.md')).read()

setup(name='softbox',
      version=version,
      description='PySInfo: A python command line tool that displays information about the current system, including hardware and critical software.',
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
