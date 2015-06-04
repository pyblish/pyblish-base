from setuptools import setup, find_packages

with open("README.txt") as f:
    readme = f.read()


import os
import imp

version_file = os.path.abspath("pyblish/version.py")
version_mod = imp.load_source("version", version_file)
version = version_mod.version


classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities"
]


setup(
    name="pyblish",
    version=version,
    description="Plug-in driven automation framework for content",
    long_description=readme,
    author="Abstract Factory and Contributors",
    author_email="marcus@abstractfactory.com",
    url="https://github.com/pyblish/pyblish",
    license="LGPL",
    packages=find_packages(),
    zip_safe=False,
    classifiers=classifiers,
    package_data={
        "pyblish": ["plugins/*.py", "*.yaml", "vendor/nose/*.txt"],
    },
    entry_points={
        "console_scripts": ["pyblish = pyblish.cli:main"]
    },
)
