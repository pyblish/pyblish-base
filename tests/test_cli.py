import os

import pyblish
import pyblish.cli
import pyblish.api

from pyblish.vendor.click.testing import CliRunner
from pyblish.vendor.nose.tools import *
from pyblish.vendor import yaml


def ctx():
    """Return current Click context"""
    return pyblish.cli._ctx


def context():
    """Return current context"""
    return ctx().obj["context"]


def test_custom_data():
    """Data as a side-car file works fine"""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open("data.yaml", "w") as f:
            yaml.dump({"key": "value"}, f)

        runner.invoke(pyblish.cli.main, ["publish"])

        assert_equals(context().data("key"), "value")


@with_setup(lambda: True, pyblish.api.config.reset)
def test_custom_configuration():
    """Configuration as a side-car file works fine"""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open("select_instances.py", "w") as f:
            f.write("""

import pyblish.api

class SelectInstances(pyblish.api.Selector):
    def process_context(self, context):
        context.set_data("key", "value")

""")

        with open("config.yaml", "w") as f:
            yaml.dump({"paths": [os.getcwd()]}, f)

        runner.invoke(pyblish.cli.main, ["publish"])

        assert_equals(context().data("key"), "value")


@with_setup(lambda: True, pyblish.api.config.reset)
def test_corrupt_custom_configuration():
    """Bad configuration stops the publish"""
    runner = CliRunner()

    class DoesNotRun(pyblish.api.Selector):
        def process(self, context):
            context.create_instance("MyInstance")

    with runner.isolated_filesystem():
        with open("config.yaml", "w") as f:
            f.write("[{gf$$%$}")

        runner.invoke(pyblish.cli.main, ["publish"])

    assert_equals(len(context()), 0)


def test_visualise_environment_paths():
    """Visualising environment paths works well"""
    current_path = os.environ.get("PYBLISHPLUGINPATH")

    try:
        os.environ["PYBLISHPLUGINPATH"] = "/custom/path"

        runner = CliRunner()
        result = runner.invoke(pyblish.cli.main, ["--environment-paths"])

        assert result.output.startswith("/custom/path")

    finally:
        if current_path is not None:
            os.environ["PYBLISHPLUGINPATH"] = current_path
