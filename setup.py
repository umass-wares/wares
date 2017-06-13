from setuptools import setup, find_packages
import os

NAME = 'wares'
VERSION = '0.1.dev'
datafiles = [(d, [os.path.join(d,f) for f in files])
             for d, folders, files in os.walk('ogp_data')]

setup(
    name=NAME,
    version=VERSION,
    description='Python tools for UMass WARES Spectrometer',
    author='Gopal Narayanan <gopal@astro.umass.edu>',
    packages=find_packages(),
    scripts=['scripts/webstrip.py',],
    include_package_data=True,
    data_files=datafiles
)
