from setuptools import find_packages
from setuptools import setup

setup(
    name='mini_pjt_interfaces',
    version='0.0.1',
    packages=find_packages(
        include=('mini_pjt_interfaces', 'mini_pjt_interfaces.*')),
)
