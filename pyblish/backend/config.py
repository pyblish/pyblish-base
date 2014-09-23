"""Pyblish configuration

Attributes:
    Attributes present within the config.json file:

    identifier:     How to distinguish between publishable instances
    prefix:         Relative root-directory for extracted instances
    date_format:    Format with which to date extracted instances
    paths_environment_variable: Which variable to look for added
        plugin paths.
    *_regex:        Regular expression for finding the various plugins.

"""

import os
import sys

from pyblish.vendor import yaml


__all__ = ['load_default',
           'load_user',
           'load_custom',
           'load',
           'load_lazy',
           'data',
           'set_data',
           'has_data']


DEFAULTCONFIG = "config.yaml"
USERCONFIG = ".pyblish"

# Look for configuration in users HOME
_home_dir = os.path.expanduser('~')
_package_dir = os.path.dirname(__file__)

_user_config_path = os.path.join(_home_dir, USERCONFIG)
_default_config_path = os.path.join(_package_dir, DEFAULTCONFIG)

_data = dict()

# Append to _data
_data['USERCONFIG'] = USERCONFIG
_data['DEFAULTCONFIG'] = DEFAULTCONFIG
_data['USERCONFIGPATH'] = _user_config_path
_data['DEFAULTCONFIGPATH'] = _default_config_path


def load_default():
    """Load default configuration from package dir"""
    with open(_default_config_path, 'r') as f:
        _data.update(yaml.load(f))


def load_user():
    """Load user configuration from HOME directory"""
    if os.path.isfile(_user_config_path):
        try:
            with open(_user_config_path, 'r') as f:
                _data.update(yaml.load(f))
        except:
            sys.stderr.write("Error: Could not read user configuration "
                             "@ {0}\n".format(_user_config_path))


def load_custom(path):
    """Load configuration from file at `path`"""
    with open(path, 'r') as f:
        _data.update(yaml.load(f))


def load():
    """Load default and user configuration"""
    load_default()
    load_user()


def load_lazy():
    """Load configuration if it hasn't already been loaded"""
    if not _data:
        load()


def data(key=None):
    """Return `key` from configuration.

    Arguments:
        key (str): Optional key to look for in config.
            If no key is given, all configuration is
            returned as dict.

    """

    if key is None:
        return _data
    assert isinstance(key, basestring)
    return _data.get(key)


def set_data(key, value):
    """Set temporary configuration

    .. note:: This will not be persisted.

    Arguments:
        key (str): Key to set
        value (object): Value of key. May be of any type.

    """

    assert isinstance(key, basestring)
    _data[key] = value


def has_data(key):
    """Return True is `key` exists, otherwise return False"""
    return key in _data
