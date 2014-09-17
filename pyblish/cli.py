import os

import pyblish.version
import pyblish.backend.plugin
from pyblish.vendor import click


intro_message = """Pyblish {version} - {command}\n"""


@click.group()
@click.option("--verbose", default=False)
@click.pass_context
def main(ctx, verbose):
    """Abstract Factory - Pyblish Command-line interface

    Use the --help flag of each subcommand to learn more
    about what it can do.

    """

    if not ctx.obj:
        ctx.obj = dict()

    ctx.obj['verbose'] = verbose
    verbose = verbose


@click.command()
@click.argument("path", default=".")
@click.option("-i", "--instance", "instances", default=None, multiple=True)
@click.option("-c", "--config", default=None)
@click.pass_context
def publish(ctx, path, instances, config):
    """Publish instances of path.

    \b
    Usage:
        $ pyblish publish my_file.txt --instance=Message01
        $ pyblish publish my_file.txt --all

    """

    click.echo(intro_message.format(
        version=pyblish.version,
        command='publish'))

    path = os.path.abspath(path)

    context = pyblish.backend.plugin.Context()

    if not instances:
        for typ in ('selectors',
                    'validators',
                    'extractors',
                    'conformers'):

            click.echo(typ.title())

            for plugin in pyblish.backend.plugin.discover(type):
                click.echo("    Running plugin: %s (ok)" % plugin.__name__)
                for instance, error in plugin().process(context):
                    if error is not None:
                        print error, instance

    else:
        print "Publishing instances: %s" % str(instances)


@click.command()
@click.pass_context
@click.argument("path")
def select(ctx, path):
    """Select data from path"""


@click.command()
@click.pass_context
@click.argument("path")
def validate(ctx, path):
    """Validate data from path"""


@click.command()
@click.pass_context
@click.argument("path")
def extract(ctx, path):
    """Extract data from path"""


@click.command()
@click.pass_context
@click.argument("path")
def conform(ctx, path):
    """Conform data from path"""


main.add_command(publish)
main.add_command(select)
main.add_command(validate)
main.add_command(extract)
main.add_command(conform)
