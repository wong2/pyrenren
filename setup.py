#!/usr/bin/env python

from setuptools import setup


setup(
    name='pyrenren',
    version='1.2',
    url='https://github.com/wong2/pyrenren',
    license='MIT',
    author='wong2',
    author_email='wonderfuly@gmail.com',
    description='Python RenRen Client',
    py_modules=['pyrenren'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'requests'
    ]
)
