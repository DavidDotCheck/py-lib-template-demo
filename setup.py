# setup.py
# Author: DavidDotCheck <contact@hardt.ai}>
from setuptools import setup, find_packages

setup(
    name='py-lib-template-demo',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "setuptools"
    ],
    python_requires='>=3.8',
    author='DavidDotCheck',
    author_email='contact@hardt.ai',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)