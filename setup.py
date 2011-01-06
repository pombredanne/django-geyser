#!/usr/bin/env python

from distutils.core import setup

import geyser


setup(
    name='django-geyser',
    version=geyser.__version__,
    description='A Django application which allows objects of any type to be published to a stream.',
    author='James Lecker Jr',
    author_email='james@jameslecker.com',
    url='http://github.com/MidwestCommunications/django-geyser',
    packages=['geyser']
)
