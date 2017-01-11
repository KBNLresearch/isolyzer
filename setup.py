#!/usr/bin/env python

from distutils.core import setup

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(name='isolyzer',
      packages=['isolyzer'],
      version='0.1.0',
      license='LGPL',
      platforms=['POSIX', 'Windows'],
      description='Verify size of ISO image',
      long_description=README_TEXT,
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl'
      )


