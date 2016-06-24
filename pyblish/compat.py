"""Compatibility module"""

import re
import inspect
import warnings
from . import plugin, lib, logic

# Aliases
Selector = plugin.Collector
Conformer = plugin.Integrator

_filename_ascii_strip_re = re.compile(r'[^-\w.]')
_windows_device_files = ('CON', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4',
                         'LPT1', 'LPT2', 'LPT3', 'PRN', 'NUL')


def sort(*args, **kwargs):
    warnings.warn("pyblish.api.sort has been deprecated; "
                  "use pyblish.api.sort_plugins")
    return plugin.sort(*args, **kwargs)


def deregister_all(*args, **kwargs):
    warnings.warn("pyblish.api.deregister_all has been deprecated; "
                  "use pyblish.api.deregister_all_paths")
    return plugin.deregister_all_paths(*args, **kwargs)


# AbstractEntity
#
# The below members represent backwards compatibility
# features, kept separate for maintainability as they
# will no longer be updated and eventually discarded.


@lib.deprecated
def set_data(self, key, value):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Modify/insert data into entity

    Arguments:
        key (str): Name of data to add
        value (object): Value of data to add

    """

    self.data[key] = value


@lib.deprecated
def remove_data(self, key):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Remove data from entity

    Arguments;
        key (str): Name of data to remove

    """

    self.data.pop(key)


@lib.deprecated
def has_data(self, key):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Check if entity has key

    Arguments:
        key (str): Key to check

    Return:
        True if it exists, False otherwise

    """

    return key in self.data


@lib.deprecated
def add(self, other):
    """DEPRECATED - USE .append

    Add member to self

    This is to mimic the interface of set()

    """

    return self.append(other)


@lib.deprecated
def remove(self, other):
    """DEPRECATED - USE .pop

    Remove member from self

    This is to mimic the interface of set()

    """

    index = self.index(other)
    return self.pop(index)


plugin.AbstractEntity.add = add
plugin.AbstractEntity.remove = remove
plugin.AbstractEntity.set_data = set_data
plugin.AbstractEntity.remove_data = remove_data
plugin.AbstractEntity.has_data = has_data


# Context

@lib.deprecated
def create_asset(self, *args, **kwargs):
    return self.create_instance(*args, **kwargs)


@lib.deprecated
def add(self, other):
    return super(plugin.Context, self).append(other)


plugin.Context.create_asset = create_asset
plugin.Context.add = add


@lib.deprecated
def format_filename(filename):
    return filename


@lib.deprecated
def format_filename2(filename):
    return filename


lib.format_filename = format_filename
lib.format_filename2 = format_filename2


@lib.deprecated
def process(func, plugins, context, test=None):
    r"""Primary processing logic

    Takes callables and data as input, and performs
    logical operations on them until the currently
    registered test fails.

    If `plugins` is a callable, it is called early, before
    processing begins. If `context` is a callable, it will
    be called once per plug-in.

    Arguments:
        func (callable): Callable taking three arguments;
             plugin(Plugin), context(Context) and optional
             instance(Instance). Each must provide a matching
             interface to their corresponding objects.
        plugins (list, callable): Plug-ins to process. If a
            callable is provided, the return value is used
            as plug-ins. It is called with no arguments.
        context (Context, callable): Context whose instances
            are to be processed. If a callable is provided,
            the return value is used as context. It is called
            with no arguments.
        test (callable, optional): Provide custom test, defaults
            to the currently registered test.

    Yields:
        A result per complete process. If test fails,
        a TestFailed exception is returned, containing the
        variables used in the test. Finally, any exception
        thrown by `func` is yielded. Note that this is
        considered a bug in *your* code as you are the one
        supplying it.

    """

    __plugins = plugins
    __context = context

    if test is None:
        test = logic.registered_test()

    if hasattr(__plugins, "__call__"):
        plugins = __plugins()

    def gen(plugin, instances):
        if plugin.__instanceEnabled__ and len(instances) > 0:
            for instance in instances:
                yield instance
        else:
            yield None

    vars = {
        "nextOrder": None,
        "ordersWithError": list()
    }

    # Clear introspection values
    # TODO(marcus): Return *next* pair, this currently
    #   returns the current pair.
    self = process
    self.next_plugin = None
    self.next_instance = None

    for Plugin in plugins:
        self.next_plugin = Plugin
        vars["nextOrder"] = Plugin.order

        if not test(**vars):
            if hasattr(__context, "__call__"):
                context = __context()

            args = inspect.getargspec(Plugin.process).args

            # Backwards compatibility with `asset`
            if "asset" in args:
                args.append("instance")

            instances = logic.instances_by_plugin(context, Plugin)

            # Limit processing to plug-ins with an available instance
            if not instances and "*" not in Plugin.families:
                continue

            for instance in gen(Plugin, instances):
                if instance is None and "instance" in args:
                    continue

                # Provide introspection
                self.next_instance = instance

                try:
                    result = func(Plugin, context, instance)

                except Exception as exc:
                    # Any exception occuring within the function
                    # you pass is yielded, you are expected to
                    # handle it.
                    yield exc

                else:
                    # Make note of the order at which
                    # the potential error error occured.
                    if result["error"]:
                        if Plugin.order not in vars["ordersWithError"]:
                            vars["ordersWithError"].append(Plugin.order)
                    yield result

            # Clear current
            self.next_instance = None

        else:
            yield logic.TestFailed(test(**vars), vars)
            break


process.next_plugin = None
process.next_instance = None

logic.process = process
