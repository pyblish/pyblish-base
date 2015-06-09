"""Pyblish command-line interface

Usage:
    $ pyblish --help

Attributes:
    CONFIG_PATH: Default location of pyblsh-configuration
    DATA_PATH: Default location of user-data for the cli.
    SCREEN_WIDTH: Used in right-aligned printed elements.
    TAB: Default tab-width.
    LOG_LEVEL: Mapping between cli flags and logging flags.

    intro_message: Message displayed during each command.

Note:
    It's assumed that the cli.py will ever only be loaded once per process.
    Like when running it from a terminal, it will be loaded and then the
    entire Python process will be killed.

"""

import os
import time
import logging

import pyblish.api
import pyblish.lib
import pyblish.util
import pyblish.plugin
import pyblish.version

from pyblish.vendor import yaml
from pyblish.vendor import click

# Current Click context
_ctx = None

def _setup_log(root="pyblish"):
    log = logging.getLogger(root)
    log.setLevel(logging.INFO)
    return log

log = _setup_log()
main_log = pyblish.lib.setup_log(level=logging.ERROR)

# Constants
CONFIG_PATH = "config.yaml"
DATA_PATH = "data.yaml"

PATH_TEMPLATE = "{path} <{typ}>"
LOG_TEMPATE = "{tab}<log>: %(message)s"

SCREEN_WIDTH = 80
TAB = "    "
LOG_LEVEL = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

intro_message = """pyblish version {version}

Custom data @ {data_path}
Custom configuration @ {config_path}

Available plugin paths:
{paths}

Available plugins:
{plugins}"""



def _format_paths(paths):
    """Return paths at one new each"""
    message = ""
    for path in paths:
        message += "{0}\n".format(path)
    return message[:-1]  # Discard last newline


def _format_plugins(plugins):
    message = ""
    for plugin in plugins:
        message += "{0}\n".format(plugin.__name__)
    return message[:-1]


def _format_time(start, finish):
    """Return right-aligned time-taken message"""
    message = "Time taken: %.2fs" % (finish - start)
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

            if config is not None:
                pyblish.api.config.update(config)

            return True

    except IOError:
        pass

    except pyblish.vendor.yaml.scanner.ScannerError:
        raise

    return False


_help = yaml.load("""
config: >
    Absolute path to custom configuration file.

add-config: >
    Absolute path to configuration file to use in
    augmenting the existing configuration.

plugin-path: >
    Replace all normally discovered paths with this
    This may be called multiple times.

add-plugin-path: >
    Append to normally discovered paths.

logging-level: >
    Specify with which level to produce logging messages.
    A value lower than the default "warning" will produce more
    messages. This can be useful for debugging.

data: >
    Initialise context with data. This takes two arguments,
    key and value.

verbose: >
    Display detailed information. Useful for debugging purposes.

version: >
    Print the current version of Pyblish

paths: >
    List all available paths

plugins: >
    List all available plugins

registered-paths: >
    Print only registered-paths

environment-paths: >
    Print only paths added via environment

configured-paths: >
    Print only paths added via configuration

""")


@click.group(invoke_without_command=True)
@click.option("--verbose", is_flag=True, help=_help["verbose"])
@click.option("--version", is_flag=True, help=_help["version"])
@click.option("--paths", is_flag=True, help=_help["paths"])
@click.option("--plugins", is_flag=True, help=_help["plugins"])
@click.option("--registered-paths", is_flag=True,
              help=_help["registered-paths"])
@click.option("--environment-paths", is_flag=True,
              help=_help["environment-paths"])
@click.option("--configured-paths", is_flag=True,
              help=_help["configured-paths"])
@click.option("-pp",
              "--plugin-path",
              "plugin_paths",
              multiple=True,
              help=_help["plugin-path"])
@click.option("-ap",
              "--add-plugin-path",
              "add_plugin_paths",
              multiple=True,
              help=_help["add-plugin-path"])
@click.option("-c",
              "--config",
              default=None,
              help=_help["config"])
@click.option("-d",
              "--data",
              nargs=2,
              multiple=True,
              help=_help["data"])
@click.option("-ll",
              "--logging-level",
              type=click.Choice(LOG_LEVEL.keys()),
              default="error",
              help=_help["logging-level"])
@click.pass_context
def main(ctx,
         verbose,
         version,
         paths,
         plugins,
         environment_paths,
         configured_paths,
         registered_paths,
         plugin_paths,
         add_plugin_paths,
         config,
         data,
         logging_level):
    """Pyblish command-line interface

    Use the appropriate sub-command to initiate a publish.

    Use the --help flag of each subcommand to learn more
    about what it can do.

    \b
    Usage:
        $ pyblish publish --help
        $ pyblish test --help

    """

    global _ctx
    _ctx = ctx

    level = LOG_LEVEL[logging_level]
    log.setLevel(level)

    # Process top-level arguments
    if version:
        click.echo("pyblish version %s" % pyblish.__version__)

    # Respond to sub-commands
    if not ctx.obj:
        ctx.obj = dict()

    # Initialise context with data passed as argument
    context = pyblish.api.Context()
    ctx.obj["context"] = context

    for key, value in data:
        try:
            yaml_loaded = yaml.load(value)
        except Exception as err:
            log.error("Error: Data must be YAML formatted: "
                      "--data %s %s" % (key, value))
            ctx.obj["error"] = err
        else:
            context.set_data(str(key), yaml_loaded)

    # Load user data
    data_loaded = _load_data(context)
    config_loaded = _load_config()

    if not plugin_paths:
        plugin_paths = pyblish.api.plugin_paths()
    plugin_paths += add_plugin_paths
    ctx.obj["plugin_paths"] = plugin_paths

    available_plugins = pyblish.api.discover(paths=plugin_paths)

    if plugins:
        click.echo(_format_plugins(available_plugins))

    if verbose:
        click.echo(
            intro_message.format(
                version=pyblish.__version__,
                config_path=CONFIG_PATH if config_loaded else "None",
                data_path=DATA_PATH if data_loaded else "None",
                paths=_format_paths(plugin_paths),
                plugins=_format_plugins(available_plugins))
        )

    # Visualise available paths
    if any([paths, environment_paths, registered_paths, configured_paths]):
        _paths = list()

        if paths:
            environment_paths = True
            registered_paths = True
            configured_paths = True

        for path in plugin_paths:

            # Determine the source of each path
            _typ = "custom"
            if path in pyblish.api.environment_paths():
                _typ = "environment"

            elif path in pyblish.api.registered_paths():
                _typ = "registered"

            elif path in pyblish.api.configured_paths():
                _typ = "configured"

            # Only display queried paths
            if _typ == "environment" and not environment_paths:
                continue

            if _typ == "configured" and not configured_paths:
                continue

            if _typ == "registered" and not registered_paths:
                continue

            click.echo(PATH_TEMPLATE.format(
                path=path, typ=_typ))
            _paths.append(path)

    # Pass data to sub-commands
    ctx.obj["verbose"] = verbose
    ctx.obj["plugin_paths"] = plugin_paths


_help = yaml.load("""
path: >
    Input path for publishing operation

instance: >
    Only publish specified instance. The default behaviour
    is to publish all instances. This may be called multiple
    times.

delay: >
    Add an artificial delay to each plugin. Typically used
    in debugging.

""")


@click.command()
@click.argument("path", default=".")
@click.option("-i",
              "--instance",
              "instances",
              multiple=True,
              help=_help["instance"])
@click.option("-de",
              "--delay",
              default=None,
              type=float,
              help=_help["delay"])
@click.pass_context
def publish(ctx,
            path,
            instances,
            delay):
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

    _start = time.time()  # Benchmark

    # Use `path` argument as initial data for context
    context = ctx.obj["context"]

    if os.path.isdir(path):
        context.set_data("current_dir", path)
    else:
        context.set_data("current_file", path)

    # Begin processing
    plugins = pyblish.api.discover(paths=ctx.obj["plugin_paths"])
    context = pyblish.util.publish(context=context, plugins=plugins)

    if any(result["error"] for result in context.data("results")):
        click.echo("There were errors.")

        for result in context.data("results"):
            if result["error"] is not None:
                click.echo(result["error"])

    _end = time.time()

    if ctx.obj["verbose"]:
        click.echo()
        click.echo("-" * 80)
        click.echo(_format_time(_start, _end))


@click.command()
@click.pass_context
def config(ctx):
    """List available config.

    \b
    Usage:
        $ pyblish config
        DEFAULTCONFIG = config.yaml
        DEFAULTCONFIGPATH = pyblish\config.yaml
        commit_template = {prefix}/{date}/{family}/{instance}
        configuration_environment_variable = PYBLISHCONFIGPATH
        conformers_regex = ^conform_.*\.py$
        date_format = %Y%m%d_%H%M%S
        extractors_regex = ^extract_.*\.py$
        identifier = publishable
        paths = ["{pyblish}/plugins"]
        paths_environment_variable = PYBLISHPLUGINPATH
        prefix = published
        publish_by_default = True
        selectors_regex = ^select_.*\.py$
        validators_regex = ^validate_.*\.py$

    """

    for key, value in sorted(pyblish.api.config.iteritems()):
        entry = "{k} = {v}".format(
            tab=TAB, k=key, v=value)
        entry += " " * (SCREEN_WIDTH - len(entry))
        click.echo(entry)


main.add_command(publish)
main.add_command(config)
