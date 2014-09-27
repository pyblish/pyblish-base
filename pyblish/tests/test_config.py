import os

import pyblish
import pyblish.lib

from pyblish.vendor import yaml
from pyblish.vendor.nose.tools import with_setup


def setup():
    pass


def teardown():
    pyblish.Config()._instance = None


@with_setup(setup, teardown)
def test_config_is_singleton():
    """Config is singleton"""
    config = pyblish.Config()

    assert config is pyblish.Config()


@with_setup(setup, teardown)
def test_modifying_config_at_run_time():
    """Altering config at run-time works"""
    config = pyblish.Config()

    path = '/invalid/path'
    config['paths'].append(path)

    assert path in config['paths']
    config.reset()
    assert path not in config['paths']


@with_setup(setup, teardown)
def test_config_init():
    """Config is reading from configuration"""
    config = pyblish.Config()

    config_path = pyblish.lib.main_package_path()
    config_path = os.path.join(config_path, 'config.yaml')

    with open(config_path) as f:
        manual_config = yaml.load(f)

    for key in manual_config:
        assert key in config


@with_setup(setup, teardown)
def test_user_config():
    """User config augments default config"""
    config = pyblish.Config()

    user_config_path = config['USERCONFIGPATH']
    remove_config_file = False

    try:
        if not os.path.isfile(user_config_path):
            remove_config_file = True
            with open(user_config_path, 'w') as f:
                yaml.dump({'test_variable': 'test_value'}, f)

        config.reset()

        with open(user_config_path, 'r') as f:
            user_config = yaml.load(f)

        assert user_config
        for key in user_config:
            assert key in config

    finally:
        if remove_config_file:
            os.remove(user_config_path)
