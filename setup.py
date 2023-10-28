# setup.py
# Author: {{project.author}} <{{project.email}}}>
from setuptools import setup, find_packages

setup(
    name='{{project.distribution_name}}',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "setuptools"
    ],
    python_requires='>=3.8',
    author='{{project.author}}',
    author_email='{{project.email}}',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)