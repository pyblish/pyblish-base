import os
import json
import re
import tempfile
import contextlib
import shutil

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


mock_gui_main = """from .app import show


if __name__ == '__main__':
    show()
"""
mock_gui_app = """import pyblish.cli
from pyblish.vendor.click.testing import CliRunner


output = "Mock GUI shown."


def show():

    print(output)
    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["publish"])
    print(result.output)
"""


@contextlib.contextmanager
def mock_gui():
    """Provide path to temporary mock gui"""
    try:
        tempdir = tempfile.mkdtemp()

        module_path = os.path.join(tempdir, "mock_gui")
        os.makedirs(module_path)

        with open(os.path.join(module_path, "__init__.py"), "w") as f:
            f.write("")

        with open(os.path.join(module_path, "__main__.py"), "w") as f:
            f.write(mock_gui_main)

        with open(os.path.join(module_path, "app.py"), "w") as f:
            f.write(mock_gui_app)

        yield tempdir
    finally:
        shutil.rmtree(tempdir)


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

    os.environ["PYBLISH_HOSTS"] = hosts[0]

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


@with_setup(lib.setup, lib.teardown)
def test_show_gui():
    """Showing GUI through cli works"""

    with mock_gui() as path:
        print path
        PYTHONPATH = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = (
            PYTHONPATH + os.pathsep + path
        )

        runner = CliRunner()
        result = runner.invoke(pyblish.cli.main, ["gui", "mock_gui"])
        print(result.output.rstrip())
        print("Exit code: " + str(result.exit_code))

        assert result.exit_code == 0

        from .mock_gui.app import output
        assert output in result.output


@with_setup(lib.setup, lib.teardown)
def test_passing_data_to_gui():
    """Passing data to GUI works"""

    with mock_gui() as path:
        PYTHONPATH = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = (
            PYTHONPATH + os.pathsep + path
        )

        runner = CliRunner()
        result = runner.invoke(
            pyblish.cli.main,
            ["--data", "testing", "plugin", "gui", "mock_gui"]
        )
        print(result.output)

        m = re.search("{.+}", result.output)
        data = json.loads(m.group(0).replace("'", "\""))
        assert data["testing"] == "plugin"
