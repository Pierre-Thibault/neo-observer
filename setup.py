#!/usr/bin/env python

from setuptools import setup

setup(name='neo-observer',
      py_modules=['neo_observer'],
      packages=[],
      install_requires=[],
      version='1.0.0',
      description='Python module implementing the observer pattern using a centralized registry',
      keywords=['messaging'],
      author='Pierre Thibault',
      author_email='pierre.thibault1@gmail.com',
      url='https://github.com/Pierre-Thibault/neo-observer',
      test_suite='test_neo_observer',
      license='MIT',
      classifiers=['License :: OSI Approved :: MIT License',
                   'Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                    ],
     )

