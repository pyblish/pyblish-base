"""Pyblish command-line interface

Usage:
    $ pyblish --help

Attributes:
    CONFIG_PATH: Default location of user-configuration for
        the Pyblish cli.
    DATA_PATH: Default location of user-data for the cli.
    SCREEN_WIDTH: Used in right-aligned printed elements.
    TAB: Default tab-width.
    LOG_LEVEL: Mapping between cli flags and logging flags.

    intro_message: Message displayed during each command.

"""

import os
import sys
import time
import logging

import pyblish.api
import pyblish.lib
import pyblish.plugin
import pyblish.version

from pyblish.vendor import yaml
from pyblish.vendor import nose
from pyblish.vendor import click

try:
    # Used in package control sub-commands
    import pip
except ImportError:
    pip = None

log = logging.getLogger()
main_log = pyblish.lib.setup_log(level=logging.ERROR)

# Constants
CONFIG_PATH = os.path.join(os.getcwd(), 'config.yaml')
DATA_PATH = os.path.join(os.getcwd(), 'data.yaml')

PATH_TEMPLATE = "{tab}{path} <{typ}>"
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
User Configuration @ {user_path}

Available plugin paths:
{paths}

Available plugins:
{plugins}"""


def _setup_log(root=''):
    log = logging.getLogger(root)

    log.setLevel(logging.WARNING)

    formatter = logging.Formatter(LOG_TEMPATE.format(tab=TAB))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    return log


def _format_paths(paths):
    """Return paths at one new each"""
    message = ''
    for path in paths:
        message += "{0}- {1}\n".format(TAB, path)
    return message[:-1]  # Discard last newline


def _format_plugins(plugins):
    message = ''
    for plugin in plugins:
        message += "{0}- {1}\n".format(TAB, plugin.__name__)
    return message[:-1]


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
    A value lower than the default 'warning' will produce more
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
@click.option("--verbose", is_flag=True, help=_help['verbose'])
@click.option("--version", is_flag=True, help=_help['version'])
@click.option("--paths", is_flag=True, help=_help['paths'])
@click.option("--plugins", is_flag=True, help=_help['plugins'])
@click.option("--registered-paths", is_flag=True,
              help=_help['registered-paths'])
@click.option("--environment-paths", is_flag=True,
              help=_help['environment-paths'])
@click.option("--configured-paths", is_flag=True,
              help=_help['configured-paths'])
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
@click.option("-c",
              "--config",
              default=None,
              help=_help['config'])
@click.option("-d",
              "--data",
              nargs=2,
              multiple=True,
              help=_help['data'])
@click.option("-ll",
              "--logging-level",
              type=click.Choice(LOG_LEVEL.keys()),
              default="error",
              help=_help['logging-level'])
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

    _setup_log()

    level = LOG_LEVEL[logging_level]
    logging.getLogger().setLevel(level)

    config_loaded = _load_config()

    # Process top-level arguments
    if version:
        click.echo("pyblish version %s" % pyblish.__version__)

    # Respond to sub-commands
    if not ctx.obj:
        ctx.obj = dict()

    # Initialise context with data passed as argument
    context = pyblish.api.Context()

    for key, value in data:
        try:
            yaml_loaded = yaml.load(value)
        except Exception as err:
            log.error("Error: Data must be YAML formatted: "
                      "--data %s %s" % (key, value))
            ctx.obj['error'] = err
        else:
            context.set_data(str(key), yaml_loaded)

    # Load user data
    data_loaded = _load_data(context)

    # Resolve plugin paths from both defaults and those
    # passed as argument via `plugin_paths` and `add_plugin_paths`
    if not plugin_paths:
        plugin_paths = pyblish.api.plugin_paths()

    for plugin_path in add_plugin_paths:
        processed_path = pyblish.plugin._post_process_path(plugin_path)
        if processed_path in plugin_paths:
            log.warning("path already present: %s" % plugin_path)
            continue
        plugin_paths.append(processed_path)

    try:
        available_plugins = pyblish.api.discover(paths=plugin_paths)
    except OSError as err:
        log.error('Error: Registered path "%s" could not '
                  'be found.' % err.filename)
        ctx.obj['error'] = err

    if plugins:
        click.echo()  # newline
        click.echo("Available plugins:")
        click.echo(_format_plugins(available_plugins))

    user_config_path = pyblish.api.config['USERCONFIGPATH']
    has_user_config = os.path.isfile(user_config_path)

    if verbose:
        click.echo(
            intro_message.format(
                version=pyblish.__version__,
                config_path=CONFIG_PATH if config_loaded else "None",
                data_path=DATA_PATH if data_loaded else "None",
                user_path=user_config_path if has_user_config else "None",
                paths=_format_paths(plugin_paths),
                plugins=_format_plugins(available_plugins))
        )

    # Visualise available paths
    if any([paths, environment_paths, registered_paths, configured_paths]):
        click.echo()  # Newline
        click.echo("Available paths:")

        _paths = list()

        if paths:
            environment_paths = True
            registered_paths = True
            configured_paths = True

        for path in plugin_paths:

            # Determine the source of each path
            _typ = 'custom'
            if path in pyblish.api.environment_paths():
                _typ = 'environment'

            elif path in pyblish.api.registered_paths():
                _typ = 'registered'

            elif path in pyblish.api.configured_paths():
                _typ = 'configured'

            # Only display queried paths
            if _typ == 'environment' and not environment_paths:
                continue

            if _typ == 'configured' and not configured_paths:
                continue

            if _typ == 'registered' and not registered_paths:
                continue

            click.echo(PATH_TEMPLATE.format(
                tab=TAB, path=path, typ=_typ))
            _paths.append(path)

        if not _paths:
            click.echo("{tab}None".format(tab=TAB))

    # Pass data to sub-commands
    ctx.obj['verbose'] = verbose
    ctx.obj['context'] = context
    ctx.obj['plugin_paths'] = plugin_paths


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
              help=_help['instance'])
@click.option("-de",
              "--delay",
              default=None,
              type=float,
              help=_help['delay'])
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

    if 'error' in ctx.obj:
        # Halt execution if an error has occurec in main()
        log.error("publish: An error has occured.")
        return -1

    _start_time = time.time()  # Benchmark

    # Resolve incoming path argument into an absolute path
    path = os.path.abspath(path)

    if not os.path.exists(path):
        log.error("Path did not exist: %s" % path)
        return -1

    # Use `path` argument as initial data for context
    context = ctx.obj['context']

    if os.path.isdir(path):
        context.set_data('current_dir', path)
    else:
        context.set_data('current_file', path)

    # Begin processing
    click.echo()  # newline
    for typ in ('selectors',
                'validators',
                'extractors',
                'conformers'):

        paths = ctx.obj['plugin_paths']
        plugins = pyblish.api.discover(typ, paths=paths)
        errors = {}

        for plugin in plugins:
            click.echo("%s..." % plugin.__name__)

            if delay:
                time.sleep(delay)

            for instance, error in plugin().process(context):
                if error is not None:
                    errors[error] = instance

            if errors and typ not in ('extractors', 'conformers'):
                # Before proceeding with extraction, ensure
                # that there are no failed validators.
                click.echo()  # newline
                click.echo("There were errors:")
                for error, instance in errors.iteritems():
                    click.echo("{tab}Instance('%s'): %s".format(tab=TAB)
                               % (instance, error))
                return -1

    click.echo()
    click.echo("-" * 80)
    click.echo(_format_time(_start_time, time.time()))

    return 0


@click.command()
@click.pass_context
def test(ctx):
    """Run Pyblish test-suite.

    Use this to test your installation to ensure all systems
    are operational.

    """

    # Mute log during tests
    log.handlers[:] = []

    module_name = sys.modules[__name__].__file__
    package_dir = os.path.dirname(module_name)
    os.chdir(package_dir)

    argv = [package_dir,
            '--exclude=vendor',
            '--with-doctest',
            '--verbose']

    main_log.setLevel(logging.CRITICAL)

    return nose.run(argv=argv)


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

    if not pip:
        click.echo("Error: 'install' requires pip")
        return -1

    version = tuple([int(n) for n in pip.__version__.split(".")])
    if version < (1, 5):
        click.echo("Error: 'install' requires pip v 1.5 or higher")
        return -1

    return pip.main(['install', "pyblish-" + package])


@click.command()
@click.argument("package")
@click.pass_context
def uninstall(ctx, package):
    """Uninstall Pyblish package via pip.

    \b
    Usage:
        $ pyblish uninstall maya
        $ pyblish uninstall napoleon

    """

    if not pip:
        click.echo("Error: 'uninstall' requires pip")
        return -1

    version = tuple([int(n) for n in pip.__version__.split(".")])
    if version < (1, 5):
        click.echo("Error: 'uninstall' requires pip v 1.5 or higher")
        return -1

    return pip.main(['uninstall', "pyblish-" + package])


@click.command()
@click.pass_context
def packages(ctx):
    """List available packages for Pyblish.

    \b
    Usage:
        $ pyblish packages

    """

    if not pip:
        click.echo("Error: 'packages' requires pip")
        return -1

    version = tuple([int(n) for n in pip.__version__.split(".")])
    if version < (1, 5):
        click.echo("Error: 'packages' requires pip v 1.5 or higher")
        return -1

    return pip.main(['search', "pyblish"])


@click.command()
@click.pass_context
def config(ctx):
    """List available config.

    \b
    Usage:
        $ pyblish config

    """

    click.echo()  # newline
    click.echo("Pyblish configuration:")

    for key, value in sorted(pyblish.api.config.iteritems()):
        if key in pyblish.api.config.user:
            source = 'user'
        else:
            source = 'default'

        entry = "{tab}{k} = {v}".format(
            tab=TAB, k=key, v=value, s=source)
        entry += " " * (SCREEN_WIDTH - len(entry) - len(source))
        entry += source
        click.echo(entry)


main.add_command(publish)
main.add_command(test)
main.add_command(install)
main.add_command(uninstall)
main.add_command(packages)
main.add_command(config)
