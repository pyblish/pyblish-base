import pyblish.cli
from pyblish.vendor.click.testing import CliRunner


output = "Mock GUI shown."


def show():

    print(output)
    runner = CliRunner()
    result = runner.invoke(pyblish.cli.main, ["publish"])
    print(result.output)
