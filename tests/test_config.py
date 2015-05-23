import os

import pyblish
import pyblish.plugin
import pyblish.lib

from pyblish.vendor import yaml
from pyblish.vendor.nose.tools import with_setup

config = pyblish.plugin.Config()

PACKAGEPATH = pyblish.lib.main_package_path()
CONFIGPATH = os.path.join(PACKAGEPATH, 'tests', 'config')


def setup():
    pass


def setup_custom():
    """Expose custom configuration onto os.environ"""
    os.environ[config['configuration_environment_variable']] = CONFIGPATH


def teardown():
    config.reset()
    config._instance = None


@with_setup(setup, teardown)
def test_config_is_singleton():
    """Config is singleton"""
    assert pyblish.plugin.Config() is pyblish.plugin.Config()


@with_setup(setup, teardown)
def test_modifying_config_at_run_time():
    """Altering config at run-time works"""
    path = '/invalid/path'
    config['paths'].append(path)

    assert path in config['paths']
    config.reset()
    assert path not in config['paths']


@with_setup(setup, teardown)
def test_config_init():
    """Config is reading from configuration"""
    config_path = pyblish.lib.main_package_path()
    config_path = os.path.join(config_path, 'config.yaml')

    with open(config_path) as f:
        manual_config = yaml.load(f)

    for key in manual_config:
        assert key in config
