import os

import pyblish
import pyblish.cli
import pyblish.api

from pyblish.vendor import six

from . import lib

from pyblish.vendor.click.testing import CliRunner
from nose.tools import (
    with_setup,
)
from pyblish.vendor import mock


def ctx():
    """Return current Click context"""
    return pyblish.cli._ctx


def context():
    """Return current context"""
    return ctx().obj["context"]


@with_setup(lib.setup_empty)
def test_all_commands_run():
    """All commands run without error"""

    for args in [[],            # No argument
                 ["--verbose"],
                 ["publish"],
                 ["--verbose", "publish"],
                 ]:

        runner = CliRunner()
        result = runner.invoke(pyblish.cli.main, args)

        print("Args: %s" % args)
        print("Exit code: %s" % result.exit_code)
        print("Output: %s" % result.output)
        assert result.exit_code == 0


def test_paths():
    """Paths are correctly returned from cli"""
    plugin = pyblish.api
    for flag, func in six.iteritems({
            "--paths": plugin.plugin_paths,
            "--registered-paths": plugin.registered_paths,
            "--environment-paths": plugin.environment_paths}):

        print("Flag: %s" % flag)
        runner = CliRunner()
        result = runner.invoke(pyblish.cli.main, [flag])
        for path in func():
            assert path in result.output


def test_plugins():
    """CLI returns correct plugins"""
    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["--plugins"])

    for plugin in pyblish.api.discover():
        print("Plugin: %s" % plugin.__name__)
        assert plugin.__name__ in result.output


def test_plugins_path():
    """Custom path via cli works"""
    custom_path = os.path.join(lib.PLUGINPATH, "custom")
    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main,
                           ["--plugin-path",
                            custom_path,
                            "--plugins"])

    plugins = pyblish.api.discover(paths=[custom_path])
    for plugin in plugins:
        print("Output: %s" % result.output)
        assert plugin.__name__ in result.output


@with_setup(lib.setup_failing_cli, lib.teardown)
def test_data():
    """Injecting data works"""

    runner = CliRunner()
    runner.invoke(pyblish.cli.main, [
        "--data", "key", "10", "publish"])

    assert context().data["key"] == 10
    assert not context().has_data("notExist")


@mock.patch("pyblish.cli.log")
def test_invalid_data(mock_log):
    """Data not JSON-serialisable is treated as string"""

    runner = CliRunner()
    runner.invoke(pyblish.cli.main,
                  ["--data", "key", "['test': 'fdf}"])

    assert context().data["key"] == "['test': 'fdf}"


def test_add_plugin_path():
    """Adding a plugin-path works"""
    custom_path = os.path.join(lib.PLUGINPATH, "custom")

    runner = CliRunner()
    runner.invoke(
        pyblish.cli.main,
        ["--add-plugin-path", custom_path, "--paths"])

    assert custom_path in ctx().obj["plugin_paths"]


def test_version():
    """Version returned matches version of Pyblish"""
    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["--version"])
    print("Output: %s" % result.output)
    print("Version: %s" % pyblish.__version__)
    assert pyblish.__version__ in result.output
