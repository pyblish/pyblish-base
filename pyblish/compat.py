"""Compatibility module"""

import warnings
from . import plugin


def sort(*args, **kwargs):
    warnings.warn("pyblish.api.sort has been deprecated; "
                  "use pyblish.api.sort_plugins")
    return plugin.sort(*args, **kwargs)


def deregister_all(*args, **kwargs):
    warnings.warn("pyblish.api.deregister_all has been deprecated; "
                  "use pyblish.api.deregister_all_paths")
    return plugin.deregister_all_paths(*args, **kwargs)
