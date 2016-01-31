"""Compatibility module"""

import warnings
from . import plugin, lib

# Aliases
Selector = plugin.Collector
Conformer = plugin.Integrator


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
