"""Pyblish command-line interface

Usage:
    $ pyblish --help

Attributes:
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
import sys
import time
import json
import shutil
import logging
import tempfile
import subprocess
import contextlib

from . import api, lib, util, __version__
from .vendor import click

_ctx = None
_help = {
    "main": {
        "paths": "List all available paths",
        "registered-paths": "Print only registered-paths",
        "verbose": "Display detailed information. Useful for "
                   "debugging purposes.",
        "plugin-path": "Replace all normally discovered paths "
                       "with this This may be called multiple times.",
        "add-plugin-path": "Append to normally discovered paths.",
        "logging-level": "Specify with which level to produce "
                         "logging messages. A value lower than the default "
                         "\"warning\" will produce more messages. This "
                         "can be useful for debugging.",
        "environment-paths": "Print only paths added via environment",
        "version": "Print the current version of Pyblish",
        "plugins": "List all available plugins",
        "data": "Initialise context with data. This takes "
                "two arguments, key and value.",
    },
    "publish": {
        "delay": "Add an artificial delay to each plugin. "
                 "Typically used in debugging.",
        "path": "Input path for publishing operation",
        "file": "Load file in host registered to it's suffix",
        "instance": "Only publish specified instance. "
                    "The default behaviour is to publish "
                    "all instances. This may be called multiple times.",
        "targets": "Use only plugins which have similar targets. Provide a "
                   "string of targets separated by a `;`"
    }
}


def _setup_log(root="pyblish"):
    log = logging.getLogger(root)
    log.setLevel(logging.INFO)
    return log


log = _setup_log()
main_log = lib.setup_log(level=logging.ERROR)

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


@contextlib.contextmanager
def _cli_plugin(data):
    tempdir = tempfile.mkdtemp()
    fname = os.path.join(tempdir, "cli_plugin.py")
    with open(fname, "w") as f:
        f.write("""\
from pyblish import api

class CliPlugin(api.ContextPlugin):
    \"\"\"Added through command-line interface to modify context\"\"\"
    order = api.CollectorOrder - 0.5
    label = "CLI Plugin"

    def process(self, context):
        import json
        context.data.update({data})
        self.log.debug(context.data)
""".format(data=json.dumps(data)))

    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


@click.group(invoke_without_command=True)
@click.option("--verbose", is_flag=True, help=_help["main"]["verbose"])
@click.option("--version", is_flag=True, help=_help["main"]["version"])
@click.option("--paths", is_flag=True, help=_help["main"]["paths"])
@click.option("--plugins", is_flag=True, help=_help["main"]["plugins"])
@click.option("--registered-paths", is_flag=True,
              help=_help["main"]["registered-paths"])
@click.option("--environment-paths", is_flag=True,
              help=_help["main"]["environment-paths"])
@click.option("-pp",
              "--plugin-path",
              "plugin_paths",
              multiple=True,
              help=_help["main"]["plugin-path"])
@click.option("-ap",
              "--add-plugin-path",
              "add_plugin_paths",
              multiple=True,
              help=_help["main"]["add-plugin-path"])
@click.option("-d",
              "--data",
              nargs=2,
              multiple=True,
              help=_help["main"]["data"])
@click.option("-ll",
              "--logging-level",
              type=click.Choice(LOG_LEVEL.keys()),
              default="error",
              help=_help["main"]["logging-level"])
@click.pass_context
def main(ctx,
         verbose,
         version,
         paths,
         plugins,
         environment_paths,
         registered_paths,
         plugin_paths,
         add_plugin_paths,
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

    # Convert multi-arguments from tuple to list, see #357
    plugin_paths = list(plugin_paths)
    add_plugin_paths = list(add_plugin_paths)
    data = list(data)

    level = LOG_LEVEL[logging_level]
    log.setLevel(level)

    # Process top-level arguments
    if version:
        click.echo("pyblish version %s" % __version__)

    # Respond to sub-commands
    if not ctx.obj:
        ctx.obj = dict()

    # Initialise context with data passed as argument
    context = api.Context()
    ctx.obj["context"] = context

    for key, value in data:
        try:
            value = json.loads(value)
        except ValueError:
            pass

        context.data[str(key)] = value

    if not plugin_paths:
        plugin_paths = api.plugin_paths()
    plugin_paths += add_plugin_paths
    ctx.obj["plugin_paths"] = plugin_paths

    available_plugins = api.discover(paths=plugin_paths)
    if plugins:
        click.echo(_format_plugins(available_plugins))

    if verbose:
        click.echo(
            intro_message.format(
                version=__version__,
                paths=_format_paths(plugin_paths),
                plugins=_format_plugins(available_plugins))
        )

    # Visualise available paths
    if any([paths, environment_paths, registered_paths]):
        _paths = list()

        if paths:
            environment_paths = True
            registered_paths = True

        for path in plugin_paths:

            # Determine the source of each path
            _typ = "custom"
            if path in api.environment_paths():
                _typ = "environment"

            elif path in api.registered_paths():
                _typ = "registered"

            # Only display queried paths
            if _typ == "environment" and not environment_paths:
                continue

            if _typ == "registered" and not registered_paths:
                continue

            click.echo(PATH_TEMPLATE.format(
                path=path, typ=_typ))
            _paths.append(path)

    # Pass data to sub-commands
    ctx.obj["verbose"] = verbose
    ctx.obj["plugin_paths"] = plugin_paths


@click.command()
@click.argument("path", default=".")
@click.option("-i",
              "--instance",
              "instances",
              multiple=True,
              help=_help["publish"]["instance"])
@click.option("-de",
              "--delay",
              default=None,
              type=float,
              help=_help["publish"]["delay"])
@click.option("-t",
              "--targets",
              multiple=True,
              help=_help["publish"]["targets"])
@click.pass_context
def publish(ctx,
            path,
            instances,
            delay,
            targets):
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

    # Convert multi-arguments from tuple to list, see #357
    targets = list(targets)
    instances = list(instances)

    _start = time.time()  # Benchmark

    # Use `path` argument as initial data for context
    context = ctx.obj["context"]

    if os.path.isdir(path):
        context.data["current_dir"] = path  # backwards compatibility
        context.data["currentDir"] = path
    else:
        context.data["current_file"] = path  # backwards compatibility
        context.data["currentFile"] = path

    # Begin processing
    plugins = api.discover(paths=ctx.obj["plugin_paths"])
    context = util.publish(context=context, plugins=plugins, targets=targets)

    if any(result["error"] for result in context.data.get("results", [])):
        click.echo("There were errors.")

        for result in context.data["results"]:
            if result["error"] is not None:
                click.echo(result["error"])

    _end = time.time()

    if ctx.obj["verbose"]:
        click.echo()
        click.echo("-" * 80)
        click.echo(_format_time(_start, _end))


@click.command()
@click.argument("package", default="pyblish_qml")
@click.pass_context
def gui(ctx, package):

    environ = os.environ.copy()
    context = ctx.obj["context"]

    registered_guis = api.registered_guis()

    if len(registered_guis) > 0:
        package = registered_guis[0]

    with _cli_plugin(data=context.data) as plugin_path:
        environ["PYBLISHPLUGINPATH"] = os.pathsep.join(
            ctx.obj["plugin_paths"] + [plugin_path]
        )

        process = subprocess.Popen(
            [sys.executable, "-m", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=environ,
            bufsize=1,
            universal_newlines=True
        )
        while True:
            line = process.stdout.readline()
            if line != '':
                print(line.rstrip())
            else:
                break
        process.wait()
        sys.exit(process.returncode)


main.add_command(publish)
main.add_command(gui)
