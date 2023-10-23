# setup.py
# Author: {{user.name}} <{{user.email}}}>
from setuptools import setup, find_packages

setup(
    name='{{project.distribution_name}}',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pytest',
        'sphinx',
        'setuptools',
        'sphinx-rtd-theme',
        'invoke',
    ],
    python_requires='>=3.8',
    author='{{user.name}}',
    author_email='{{user.email}}',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)