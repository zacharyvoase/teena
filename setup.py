import os
import sys; reload(sys).setdefaultencoding('utf-8')

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages


long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read().decode('utf-8')


setup(
    name='teena',
    version='0.0.2',
    description="Python ports of useful syscalls, using asynchronous I/O.",
    long_description=long_description,
    author='Zachary Voase',
    author_email='z@zacharyvoase.com',
    url='http://github.com/zacharyvoase/teena',
    packages=find_packages(exclude=('test',)),
    install_requires=[
        'tornado==6.3.2',
    ],
)
