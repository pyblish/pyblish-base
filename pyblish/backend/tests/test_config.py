import os
import sys

import pyblish.main
import pyblish.backend.lib
import pyblish.backend.config
import pyblish.backend.plugin

from pyblish.vendor import yaml

from pyblish.backend.tests.lib import (
    setup, teardown)
from pyblish.vendor.nose.tools import with_setup


def _reload_config():
    try:
        sys.modules.pop('pyblish.backend.config')
        import pyblish.backend.config
    except ValueError:
        pass


@with_setup(setup, teardown)
def test_config():
    """Config works as expected"""
    config = pyblish.backend.config
    config_path = pyblish.backend.lib.main_package_path()
    config_path = os.path.join(config_path, 'backend', 'config.yaml')

    with open(config_path) as f:
        manual_config = yaml.load(f)

    for key, value in manual_config.iteritems():
        assert getattr(config, key) == value


def test_user_config():
    """User config augments default config"""
    user_config_path = pyblish.backend.config.USERCONFIGPATH
    remove_config_file = False

    try:
        if not os.path.isfile(user_config_path):
            remove_config_file = True
            with open(user_config_path, 'w') as f:
                yaml.dump({'test_variable': 'test_value'}, f)

        # Force a reload of configuration
        _reload_config()

        with open(user_config_path, 'r') as f:
            user_config = yaml.load(f)

        assert user_config
        for variable in user_config:
            assert getattr(pyblish.backend.config, variable, None)

    finally:
        if remove_config_file:
            os.remove(user_config_path)
