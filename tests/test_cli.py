import os
import sys
import shutil
import tempfile

import pytest
import pyblish
import pyblish.cli
import pyblish.api
from pyblish.vendor.click.testing import CliRunner
from tests import lib

self = sys.modules[__name__]


@pytest.fixture
def tempdir():
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        shutil.rmtree(path)


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


def test_publishing(setup_empty_and_teardown):
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


def test_environment_host_registration(setup_and_teardown):
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


def test_show_gui(setup_and_teardown, tempdir):
    """Showing GUI through cli works"""

    with tempfile.NamedTemporaryFile(dir=tempdir, delete=False, suffix=".py") as f:
        module_name = os.path.basename(f.name)[:-3]
        f.write(b"""\
def show():
    print('Mock GUI shown successfully')

if __name__ == '__main__':
    show()
""")

    pythonpath = os.pathsep.join([tempdir, os.environ.get("PYTHONPATH", "")])

    runner = CliRunner()
    result = runner.invoke(
        pyblish.cli.main, ["gui", module_name],
        env={"PYTHONPATH": pythonpath}
    )

    assert result.output.splitlines()[-1].rstrip() == "Mock GUI shown successfully"
    assert result.exit_code == 0


def test_uses_gui_from_env(setup_and_teardown, tempdir):
    """Uses gui from environment var works"""

    with tempfile.NamedTemporaryFile(dir=tempdir, delete=False, suffix=".py") as f:
        module_name = os.path.basename(f.name)[:-3]
        f.write(b"""\
def show():
    print('Mock GUI shown successfully')

if __name__ == '__main__':
    show()
""")

    pythonpath = os.pathsep.join([tempdir, os.environ.get("PYTHONPATH", "")])

    runner = CliRunner()
    result = runner.invoke(
        pyblish.cli.main, ["gui"],
        env={
            "PYTHONPATH": pythonpath,
            "PYBLISH_GUI": module_name
        }
    )

    assert result.output.splitlines()[-1].rstrip() == "Mock GUI shown successfully"
    assert result.exit_code == 0


def test_passing_data_to_gui(setup_and_teardown, tempdir):
    """Passing data to GUI works"""

    with tempfile.NamedTemporaryFile(dir=tempdir, delete=False, suffix=".py") as f:
        module_name = os.path.basename(f.name)[:-3]
        f.write(b"""\
from pyblish import util

def show():
    context = util.publish()
    print(context.data['passedFromTest'])

if __name__ == '__main__':
    show()
""")

    pythonpath = os.pathsep.join([tempdir, os.environ.get("PYTHONPATH", "")])

    runner = CliRunner()
    result = runner.invoke(
        pyblish.cli.main,
        [
            "--data", "passedFromTest", "Data passed successfully",
            "gui", module_name
        ],
        env={"PYTHONPATH": pythonpath}
    )

    assert result.output.splitlines()[-1].rstrip() == "Data passed successfully"
    assert result.exit_code == 0


def test_set_targets(setup_and_teardown, tempdir):
    """Setting targets works"""

    pythonpath = os.pathsep.join([tempdir, os.environ.get("PYTHONPATH", "")])

    count = {"#": 0}

    class CollectorOne(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        targets = ["imagesequence"]

        def process(self, context):
            self.log.warning("Running {0}".format(self.targets))
            count["#"] += 1
            context.create_instance("MyInstance")

    class CollectorTwo(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        targets = ["model"]

        def process(self, context):
            self.log.warning("Running {0}".format(self.targets))
            count["#"] += 2
            context.create_instance("MyInstance")

    pyblish.api.register_plugin(CollectorOne)
    pyblish.api.register_plugin(CollectorTwo)

    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main,
                           ["publish", "--targets", "imagesequence"],
                           env={"PYTHONPATH": pythonpath})

    print(result.output)
    assert count["#"] == 1, count


def test_set_targets_gui(setup_and_teardown, tempdir):
    """Setting targets with gui"""

    with tempfile.NamedTemporaryFile(dir=tempdir, delete=False, suffix=".py") as f:
        module_name = os.path.basename(f.name)[:-3]
        f.write(b"""\
from pyblish import api

def show():
    targets = api.registered_targets()
    print(targets[0])

if __name__ == '__main__':
    show()
""")

    pythonpath = os.pathsep.join([tempdir, os.environ.get("PYTHONPATH", "")])

    runner = CliRunner()
    results = runner.invoke(
        pyblish.cli.main,
        ["gui", module_name],
        env={
            "PYTHONPATH": pythonpath,
            "PYBLISH_TARGETS": "imagesequence"
        }
    )

    result = results.output.splitlines()[-1].rstrip()
    assert result == "imagesequence"
    assert results.exit_code == 0
