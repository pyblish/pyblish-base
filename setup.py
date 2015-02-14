from setuptools import setup, find_packages

import os
import imp


with open("README.txt") as f:
    readme = f.read()

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


# Collect all plug-ins and configuration files used in tests.
#
# This ends up becoming a list of relative paths, starting
# from the pyblish package dir.
#
# E.g.
#   ["plugins//*.py", "plugins/custom/*.py",
#    "plugins/duplicate/*.py", ... ]
#
plugins_dir = os.path.abspath("pyblish/tests/plugins")
plugins_package_data = list()
for root, dirs, files in os.walk(plugins_dir):
    relpath = os.path.relpath(root, plugins_dir)
    relpath = relpath.replace("\\", "/")
    plugins_package_data.append("plugins/" + relpath.strip(".") + "/*.py")


config_dir = os.path.abspath("pyblish/tests/config")
config_package_data = list()
for root, dirs, files in os.walk(config_dir):
    relpath = os.path.relpath(root, config_dir)
    relpath = relpath.replace("\\", "/")
    config_package_data.append("config/" + relpath.strip(".") + "/.pyblish")
    config_package_data.append("config/" + relpath.strip(".") + "/*.yaml")


tests_package_data = plugins_package_data + config_package_data


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
        "pyblish.tests": tests_package_data,
    },
)
