import os

from pyblish import api, _cli
from nose.tools import (
    with_setup
)
from pyblish._vendor.click.testing import CliRunner
from . import lib


def ctx():
    """Return current Click context"""
    return _cli._ctx


def context():
    """Return current context"""
    return ctx().obj["context"]


def test_visualise_environment_paths():
    """Visualising environment paths works well"""
    current_path = os.environ.get("PYBLISHPLUGINPATH")

    try:
        os.environ["PYBLISHPLUGINPATH"] = "/custom/path"

        runner = CliRunner()
        result = runner.invoke(_cli.main, ["--environment-paths"])

        assert result.output.startswith("/custom/path"), result.output

    finally:
        if current_path is not None:
            os.environ["PYBLISHPLUGINPATH"] = current_path


@with_setup(lib.setup_empty, lib.teardown)
def test_publishing():
    """Basic publishing works"""

    count = {"#": 0}

    class Collector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            self.log.warning("Running")
            count["#"] += 1
            context.create_instance("MyInstance")

    class MyValidator(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10
            assert instance.data["name"] == "MyInstance"
            count["#"] += 100

    api.register_plugin(Collector)
    api.register_plugin(MyValidator)

    runner = CliRunner()
    result = runner.invoke(_cli.main, ["publish"])
    print(result.output)

    assert count["#"] == 111, count
