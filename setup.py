#!/usr/bin/env python

from setuptools import setup


setup(
    name='renren-client',
    version='1.0',
    url='https://github.com/wong2/renren-client',
    license='MIT',
    author='wong2',
    author_email='wonderfuly@gmail.com',
    description='RenRen client',
    py_modules=['renren_client'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'requests',
        'pyquery'
    ]
)
