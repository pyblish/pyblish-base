import os
import tempfile

import pyblish
import pyblish.lib

from pyblish.vendor import yaml
from pyblish.vendor.nose.tools import with_setup


PACKAGEPATH = pyblish.lib.main_package_path()
CONFIGPATH = os.path.join(PACKAGEPATH, 'tests', 'config')
USERCONFIGPATH = pyblish.Config.USERCONFIGPATH


def setup():
    pass


def setup_user():
    _, pyblish.Config.USERCONFIGPATH = tempfile.mkstemp()


def setup_custom():
    """Expose custom configuration onto os.environ"""
    config = pyblish.Config()
    os.environ[config['configuration_environment_variable']] = CONFIGPATH

    # Re-read from environment
    config.reset()


def setup_custom_file():
    """Expose custom configuration by direct reference to file"""
    config = pyblish.Config()
    path = os.path.join(CONFIGPATH, 'additional_configuration', 'config.yaml')
    os.environ[config['configuration_environment_variable']] = path

    # Re-read from environment
    config.reset()


def setup_custom_cascade():
    """Expose custom configuration onto os.environ"""
    config = pyblish.Config()

    path1 = CONFIGPATH
    path2 = os.path.join(path1, 'additional_configuration')

    sep = ";" if os.name == "nt" else ":"
    path = path1 + sep + path2

    os.environ[config['configuration_environment_variable']] = path

    # Re-read from environment
    config.reset()


def teardown():
    pyblish.Config._instance = None
    pyblish.Config.USERCONFIGPATH = USERCONFIGPATH


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


@with_setup(setup_user, teardown)
def test_user_config():
    """User config augments default config"""
    config = pyblish.Config()

    user_config_path = config['USERCONFIGPATH']

    with open(user_config_path, 'w') as f:
        yaml.dump({'test_variable': 'test_value'}, f)

    config.reset()

    with open(user_config_path, 'r') as f:
        user_config = yaml.load(f)

    assert user_config
    for key in user_config:
        assert key in config


@with_setup(setup_custom, teardown)
def test_custom_config():
    """Custom configuration augments defaults"""
    config = pyblish.Config()
    assert config['custom_variable'] is True


@with_setup(setup_custom_cascade, teardown)
def test_custom_cascading_configuration():
    """The last-added configuration has last say"""
    config = pyblish.Config()

    # The last-entered path sets this variable to False
    print config['custom_variable']
    assert config['custom_variable'] is False


@with_setup(setup_custom_file, teardown)
def test_custom_file():
    """Passing file on config path is ok

    E.g. PYBLISHCONFIGPATH=c:\config.yaml

    """

    config = pyblish.Config()

    # The last-entered path sets this variable to False
    print config['custom_variable']
    assert config['custom_variable'] is False


@with_setup(setup_user, teardown)
def test_user_overrides_custom():
    """User configuration overrides Custom configuration"""
    config = pyblish.Config()

    user_config_path = config['USERCONFIGPATH']
    os.environ[config['configuration_environment_variable']] = CONFIGPATH

    with open(user_config_path, 'w') as f:
        yaml.dump({'custom_variable': 'user value'}, f)

    config.reset()

    # Even though our custom configuration defines
    # this the user-configuration will override it.
    print config['custom_variable']
    assert config['custom_variable'] == 'user value'
