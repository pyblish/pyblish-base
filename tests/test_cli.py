import os

import pyblish
import pyblish.cli
import pyblish.api
from nose.tools import (
    with_setup
)
from pyblish.vendor.click.testing import CliRunner
from . import lib


def ctx():
    """Return current Click context"""
    return pyblish.cli._ctx


def context():
    """Return current context"""
    return ctx().obj["context"]


def test_visualise_environment_paths():
    """Visualising environment paths works well"""
    current_path = os.environ.get("PYBLISHPLUGINPATH")

    try:
        os.environ["PYBLISHPLUGINPATH"] = "/custom/path"

        runner = CliRunner()
        result = runner.invoke(pyblish.cli.main, ["--environment-paths"])

        assert result.output.startswith("/custom/path"), result.output

    finally:
        if current_path is not None:
            os.environ["PYBLISHPLUGINPATH"] = current_path


@with_setup(lib.setup_empty, lib.teardown)
def test_publishing():
    """Basic publishing works"""

    count = {"#": 0}

    class Collector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            self.log.warning("Running")
            count["#"] += 1
            context.create_instance("MyInstance")

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10
            assert instance.data["name"] == "MyInstance"
            count["#"] += 100

    pyblish.api.register_plugin(Collector)
    pyblish.api.register_plugin(MyValidator)

    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["publish"])
    print(result.output)

    assert count["#"] == 111, count


@with_setup(lib.setup, lib.teardown)
def test_environment_host_registration():
    """Host registration from PYBLISH_HOSTS works"""

    count = {"#": 0}
    hosts = ["test1", "test2"]

    # Test single hosts
    class SingleHostCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        host = hosts[0]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(SingleHostCollector)

    os.environ["PYBLISH_HOSTS"] = "test1"

    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["publish"])
    print(result.output)

    assert count["#"] == 1, count

    # Test multiple hosts
    pyblish.api.deregister_all_plugins()

    class MultipleHostsCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        host = hosts

        def process(self, context):
            count["#"] += 10

    pyblish.api.register_plugin(MultipleHostsCollector)

    os.environ["PYBLISH_HOSTS"] = os.pathsep.join(hosts)

    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["publish"])
    print(result.output)

    assert count["#"] == 11, count
