from setuptools import setup, find_packages

NAME = 'wares'
VERSION = '0.1.dev'

setup(
    name=NAME,
    version=VERSION,
    description='Python tools for UMass WARES Spectrometer',
    author='Gopal Narayanan <gopal@astro.umass.edu>',
    packages=find_packages(),
)
