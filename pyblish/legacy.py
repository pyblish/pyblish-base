"""Backwards compatibility module"""

import logging

import pyblish.lib


def _process_legacy(plugin, context, instance=None):
    import time

    if "results" not in context.data():
        context.set_data("results", list())

    if not hasattr(plugin, "process_context"):
        plugin.process_context = lambda self, context: None

    if not hasattr(plugin, "process_instance"):
        plugin.process_instance = lambda self, instance: None

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "error": None,
        "records": list(),
        "duration": None
    }

    records = list()
    handler = pyblish.lib.MessageHandler(records)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    __start = time.time()

    try:
        plugin().process_context(context)
        result["success"] = True
    except Exception as exc:
        pyblish.lib.extract_traceback(exc)
        result["error"] = exc

    if instance is not None:
        try:
            plugin().process_instance(instance)
            result["success"] = True
        except Exception as exc:
            pyblish.lib.extract_traceback(exc)
            result["error"] = exc

    __end = time.time()

    for record in records:
        result["records"].append(record)

    # Restore balance to the world
    root_logger.removeHandler(handler)

    result["duration"] = (__end - __start) * 1000  # ms

    context.data("results").append(result)

    return result


def _repair_legacy(plugin, context, instance=None):
    import time

    if "results" not in context.data():
        context.set_data("results", list())

    if not hasattr(plugin, "repair_context"):
        plugin.repair_context = lambda self, context: None

    if not hasattr(plugin, "repair_instance"):
        plugin.repair_instance = lambda self, instance: None

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "error": None,
        "records": list(),
        "duration": None
    }

    records = list()
    handler = pyblish.lib.MessageHandler(records)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    __start = time.time()

    try:
        plugin().repair_context(context)
        result["success"] = True
    except Exception as exc:
        pyblish.lib.extract_traceback(exc)
        result["error"] = exc

    if instance is not None:
        try:
            plugin().repair_instance(instance)
            result["success"] = True
        except Exception as exc:
            pyblish.lib.extract_traceback(exc)
            result["error"] = exc

    __end = time.time()

    for record in records:
        result["records"].append(record)

    # Restore balance to the world
    root_logger.removeHandler(handler)

    result["duration"] = (__end - __start) * 1000  # ms

    context.data("results").append(result)

    return result
