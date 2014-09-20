"""Pyblish command-line interface"""


import os
import sys
import time
import logging

import pyblish.api
import pyblish.version
import pyblish.backend.plugin

from pyblish.vendor import yaml
from pyblish.vendor import nose
from pyblish.vendor import click


# Constants
CONFIG_PATH = os.path.join(os.getcwd(), 'config.yaml')
DATA_PATH = os.path.join(os.getcwd(), 'data.yaml')

SCREEN_WIDTH = 80
TAB = "    "
LOG_LEVEL = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

intro_message = """Pyblish {version} - {command}

Custom data @ {data_path}
Custom configuration @ {config_path}

Available plugin paths: {paths}

Available plugins: {plugins}
"""


_help = {
    "path": (
        "Input path for publishing operation"
    ),
    "instance": (
        "Only publish specified instance. "
        "The default behaviour is to publish all instances "
        "This may be called multiple times. "
    ),
    "config": (
        "Absolute path to custom configuration file."
    ),
    "add-config": (
        "Absolute path to configuration file to use in "
        "augmenting the existing configuration."
    ),
    "plugin-path": (
        "Replace all normally discovered paths with this "
        "This may be called multiple times."
    ),
    "add-plugin-path": (
        "Append to normally discovered paths."
    ),
    "delay": (
        "Add an artificial delay to each plugin. Typically used "
        "in debugging."
    ),
    "logging-level": (
        "Specify with which level to produce logging messages."
        "A value lower than the default 'warning' will produce more"
        "messages. This can be useful for debugging."
    ),
    "data": (
        "Initialise context with data. This takes two arguments, "
        "key and value."
    )
}


def _setup_logging():
    log = logging.getLogger()

    log.setLevel(logging.WARNING)

    formatter = logging.Formatter('{tab}<log>: %(message)s'.format(tab=TAB))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    return log


def _format_paths(paths):
    """Return paths at one new each"""
    message = ''
    for path in paths:
        message += "\n{0}- {1}".format(TAB, path)
    return message


def _format_plugins(plugins):
    message = ''
    for plugin in plugins:
        message += "\n{0}- {1}".format(TAB, plugin.__name__)
    return message


def _format_time(start, finish):
    """Return right-aligned time-taken message"""
    message = 'Time taken: %.2fs' % (finish - start)
    return message.rjust(SCREEN_WIDTH)


def _load_data(context):
    """Inject context with user-supplied data"""
    try:
        with open(DATA_PATH) as f:
            data = yaml.load(f)
            for key, value in data.iteritems():
                context.set_data(key, value)

            return True

    except IOError:
        pass

    return False


def _load_config():
    """Augment configuration with user-supplied config.yaml"""
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.load(f)
            for key, value in config.iteritems():
                setattr(pyblish.api.config, key, value)

            return True

    except IOError:
        pass

    return False


@click.group()
@click.option("--verbose", default=False)
@click.pass_context
def main(ctx, verbose):
    """Pyblish command-line interface

    Use the appropriate sub-command to initiate a publish.

    Use the --help flag of each subcommand to learn more
    about what it can do.

    \b
    Usage:
        $ pyblish publish --help
        $ pyblish test --help

    """

    if not ctx.obj:
        ctx.obj = dict()

    ctx.obj['verbose'] = verbose
    verbose = verbose


@click.command()
@click.argument("path", default=".")
@click.option("-i",
              "--instance",
              "instances",
              multiple=True,
              help=_help['instance'])
@click.option("-c",
              "--config",
              default=None,
              help=_help['config'])
@click.option("-pp",
              "--plugin-path",
              "plugin_paths",
              multiple=True,
              help=_help['plugin-path'])
@click.option("-ap",
              "--add-plugin-path",
              "add_plugin_paths",
              multiple=True,
              help=_help['add-plugin-path'])
@click.option("-de",
              "--delay",
              default=None,
              type=float,
              help=_help['delay'])
@click.option("-ll",
              "--logging-level",
              type=click.Choice(LOG_LEVEL.keys()),
              default="warning",
              help=_help['logging-level'])
@click.option("-d",
              "--data",
              nargs=2,
              multiple=True,
              help=_help['data'])
@click.pass_context
def publish(ctx,
            path,
            instances,
            config,
            plugin_paths,
            add_plugin_paths,
            delay,
            logging_level,
            data):
    """Publish instances of path.

    \b
    Arguments:
        path: Optional path, either absolute or relative,
            at which to initialise a publish. Defaults to
            the current working directory.

    \b
    Usage:
        $ pyblish publish my_file.txt --instance=Message01
        $ pyblish publish my_file.txt --all

    """

    log = _setup_logging()
    log.setLevel(LOG_LEVEL[logging_level])

    _start_time = time.time()

    # Resolve incoming path argument into an absolute path
    path = os.path.abspath(path)

    if not os.path.exists(path):
        click.echo("Path did not exist: %s" % path)
        return

    context = pyblish.backend.plugin.Context()

    # Initialise context with data passed as argument
    for key, value in data:
        try:
            yaml_loaded = yaml.load(value)
        except ValueError:
            click.echo("Data must be YAML formatted: "
                       "--data %s %s" % (key, value))
            return

        context.set_data(str(key), yaml_loaded)

    # Load user config and data
    data_loaded = _load_data(context)
    config_loaded = _load_config()

    # Use `path` argument as initial data for context
    if os.path.isdir(path):
        context.set_data('current_dir', path)
    else:
        context.set_data('current_file', path)

    # Resolve plugin paths from both defaults and those
    # passed as argument via `plugin_paths` and `add_plugin_paths`
    if not plugin_paths:
        plugin_paths = pyblish.api.plugin_paths()

    for plugin_path in add_plugin_paths:
        plugin_paths.append(plugin_path)

    # Collect available plugins for visualisation in terminal.
    # .. note:: this isn't actually used for processing.
    available_plugins = pyblish.api.discover(paths=plugin_paths)

    click.echo(
        intro_message.format(
            version=pyblish.version,
            command='publish',
            config_path=CONFIG_PATH if config_loaded else "None",
            data_path=DATA_PATH if data_loaded else "None",
            paths=_format_paths(plugin_paths),
            plugins=_format_plugins(available_plugins))
    )

    # Begin processing
    for typ in ('selectors',
                'validators',
                'extractors',
                'conformers'):

        for plugin in pyblish.backend.plugin.discover(typ,
                                                      paths=plugin_paths):
            click.echo("%s..." % plugin.__name__)

            if delay:
                time.sleep(delay)

            for instance, error in plugin().process(context):
                if error is not None:
                    print error, instance

    click.echo()
    click.echo("-" * 80)
    click.echo(_format_time(_start_time, time.time()))


@click.command()
@click.pass_context
def test(ctx):
    """Run Pyblish test-suite.

    Use this to test your installation to ensure all systems
    are operational.

    """

    module_name = sys.modules[__name__].__file__
    package_dir = os.path.dirname(module_name)
    init_dir = os.path.join(package_dir, '__init__.py')

    argv = [init_dir]
    argv.extend(['pyblish',
                 '--verbose',
                 '--exclude=vendor',
                 '--with-doctest'])
    nose.run(argv=argv)


@click.command()
@click.argument("package")
@click.pass_context
def install(ctx, package):
    """Install Pyblish package via pip.

    \b
    Usage:
        $ pyblish install maya
        $ pyblish install napoleon

    """

    try:
        import pip
    except ImportError:
        return click.echo("Error: 'install' requires pip")

    version = tuple([int(n) for n in pip.__version__.split(".")])
    if version < (1, 5):
        return click.echo("Error: 'install' requires pip v 1.5 or higher")

    pip.main(['install', "pyblish-" + package])


main.add_command(publish)
main.add_command(test)
main.add_command(install)
