from pyblish.vendor import click
from click.testing import CliRunner

import pyblish.cli
import pyblish.api


# def test_hello_world():
#     runner = CliRunner()
#     result = runner.invoke(pyblish.cli.main, ['publish'])
#     assert result.exit_code == 0, result
#     assert result.output == 'Hello Peter!\n'
