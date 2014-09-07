"""Pyblish configuration

Usage:
    To alter the configuration of Pyblish to suit your needs,
    simply create your own copy at <HOME>/.pyblish as a JSON-
    formatted, plain-text file. E.g.

    # .pyblish
    {
        "identifier": "MyIdentifier"
    }

    Members of the configuration is then accessed via dot-
    notation.

    >>> import pyblish.backend.config
    >>> assert pyblish.backend.config.identifier == 'publishable'

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
import json
import logging

from pyblish.vendor import yaml

log = logging.getLogger('pyblish.backend.config')

# Look for configuration in users HOME
home_dir = os.path.expanduser('~')
package_dir = os.path.dirname(__file__)

user_config_path = os.path.join(home_dir, '.pyblish')
default_config_path = os.path.join(package_dir, 'config.yaml')


with open(default_config_path, 'r') as f:
    config_dict = yaml.load(f)

# Update configuration with user-configuration
if os.path.isfile(user_config_path):
    try:
        with open(user_config_path, 'r') as f:
            config_dict.update(json.load(f))
    except:
        log.warning("Could not read user configuration @ {0}".format(
            user_config_path))

# Append to config_dict
config_dict['USERCONFIGPATH'] = user_config_path
config_dict['DEFAULTCONFIGPATH'] = default_config_path

# Wrap config up in a class, so that we may access
# members directly, using dot-notation.
config_obj = type('Config', (object,), config_dict)

sys.modules[__name__] = config_obj
