#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup

except ImportError:
    from distutils.core import setup

setup(
    name='prism_plot',
    version='1.2',
    description="An animated wrapping of Dan Foreman-Mackey's triangle.py.",
    author='Ben Farr',
    author_email='farr@uchicago.edu',
    url='https://github.com/bfarr/prism',
    include_package_data=True,
    py_modules=['prism'],
)
