#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-fulfil",
    version="0.1.6",
    description="Singer.io tap for extracting data",
    author="Fulfil.IO Inc.",
    url="https://www.fulfil.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_fulfil"],
    install_requires=[
        "singer-python>=5.0.12",
        "requests",
        "fulfil-client",
    ],
    entry_points="""
    [console_scripts]
    tap-fulfil=tap_fulfil:main
    """,
    packages=["tap_fulfil"],
    package_data={
        "schemas": ["tap_fulfil/schemas/*.json"]
    },
    include_package_data=True,
)
