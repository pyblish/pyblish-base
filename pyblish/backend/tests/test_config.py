import os
import shutil

import pyblish
import pyblish.backend.lib
import pyblish.backend.plugin

from pyblish.backend import config
from pyblish.vendor import yaml


def test_modifying_config_at_run_time():
    """Altering config at run-time works"""
    path = '/invalid/path'
    paths = config.data('paths')
    config.set_data('paths', paths + [path])
    processed = pyblish.backend.plugin._post_process_path(path)
    assert processed in pyblish.plugin_paths()
    config.set_data('paths', paths)


def test_config():
    """Config works as expected"""
    config_path = pyblish.backend.lib.main_package_path()
    config_path = os.path.join(config_path, 'backend', 'config.yaml')

    with open(config_path) as f:
        manual_config = yaml.load(f)

    variable = 'paths_environment_variable'
    assert manual_config.get(variable) == config.data(variable)


def test_user_config():
    """User config augments default config"""
    user_config_path = config.data('USERCONFIGPATH')
    remove_config_file = False

    try:
        if not os.path.isfile(user_config_path):
            remove_config_file = True
            with open(user_config_path, 'w') as f:
                yaml.dump({'test_variable': 'test_value'}, f)

        # Force a reload of configuration
        config.load_user()

        with open(user_config_path, 'r') as f:
            user_config = yaml.load(f)

        assert user_config
        for variable in user_config:
            assert config.data(variable)

    finally:
        if remove_config_file:
            os.remove(user_config_path)


def test_custom_paths():
    """Adding custom paths via user-config works"""
    user_config_path = config.data('USERCONFIGPATH')

    package_path = pyblish.backend.lib.main_package_path()
    custom_path = os.path.join(package_path,
                               'backend',
                               'tests',
                               'plugins',
                               'custom')

    try:
        old_user_config_path = None
        if os.path.isfile(user_config_path):
            shutil.move(user_config_path, user_config_path + "_old")
            old_user_config_path = user_config_path + "_old"

        # Add custom path
        with open(user_config_path, 'w') as f:
            yaml.dump({'paths': [custom_path]}, f)

        # Force a reload of configuration
        config.load_user()

        paths = config.data('paths')
        assert paths

        plugins = pyblish.discover('validators')
        plugin_names = [p.__name__ for p in plugins]
        assert 'ValidateCustomInstance' in plugin_names

    finally:
        os.remove(user_config_path)

        # Restore previous config
        if old_user_config_path:
            shutil.move(old_user_config_path, user_config_path)
