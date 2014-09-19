
import pyblish.cli
import pyblish.api

from pyblish.vendor import click
from pyblish.backend.tests.lib import teardown, setup_echo
from pyblish.vendor.click.testing import CliRunner
from pyblish.vendor.nose.tools import with_setup


@with_setup(setup_echo, teardown)
def test_data():
    """Passing data augments context"""
    runner = CliRunner()
    result = runner.invoke(pyblish.cli.publish, ['--data',
                                                 'TestKey',
                                                 'TestValue'])
    print dir(result)
    print result.exc_info
    assert False


def test_hello_world():
    @click.command()
    @click.argument('name')
    def hello(name):
        click.echo('Hello %s!' % name)

    runner = CliRunner()
    result = runner.invoke(hello, ['Peter'])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'


# def test_data_float():
#     """Passing a float value as data works"""
#     pass
