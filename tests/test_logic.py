
# Local library
from . import lib

import pyblish.plugin
import pyblish.logic

from pyblish.vendor.nose.tools import *


@with_setup(lib.setup_empty, lib.teardown)
def test_process_callables():
    """logic.process can take either data or callables"""

    count = {"#": 0}

    class SelectInstance(pyblish.api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
            count["#"] += 1

    class ValidateInstance(pyblish.api.Validator):
        def process(self, instance):
            count["#"] += 1
            assert False, "I was programmed to fail"

    class ExtractInstance(pyblish.api.Extractor):
        def process(self, instance):
            count["#"] += 1

    pyblish.api.register_plugin(SelectInstance)
    pyblish.api.register_plugin(ValidateInstance)
    pyblish.api.register_plugin(ExtractInstance)

    _context = pyblish.plugin.Context()

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=pyblish.plugin.discover(),
            context=_context):

        if isinstance(result, pyblish.logic.TestFailed):
            break

        if isinstance(result, Exception):
            assert False  # This would be a bug

    assert_equals(count["#"], 2)

    def context():
        return _context

    count["#"] = 0

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=pyblish.plugin.discover,  # <- Callable
            context=context):  # <- Callable

        if isinstance(result, pyblish.logic.TestFailed):
            break

        if isinstance(result, Exception):
            assert False  # This would be a bug

    assert_equals(count["#"], 2)


@with_setup(lib.setup_empty, lib.teardown)
def test_repair():
    """Repairing with DI works well"""

    _data = {}

    class SelectInstance(pyblish.api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "MyFamily")

    class ValidateInstance(pyblish.api.Validator):
        def process(self, instance):
            _data["broken"] = True
            assert False, "Broken"

        def repair(self, instance):
            _data["broken"] = False

    context = pyblish.api.Context()

    results = list()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectInstance, ValidateInstance],
            context=context):

        if isinstance(result, pyblish.logic.TestFailed):
            assert str(result) == "Broken"

        results.append(result)

    assert_true(_data["broken"])

    repair = list()
    for result in results:
        if result["error"]:
            repair.append(result["plugin"])

    for result in pyblish.logic.process(
            func=pyblish.plugin.repair,
            plugins=repair,
            context=context):
        print result

    assert_false(_data["broken"])


@with_setup(lib.setup_empty, lib.teardown)
def test_context_once():
    """Context is only processed once, with DI"""

    count = {"#": 0}

    class SelectMany(pyblish.api.Selector):
        def process(self, context):
            for name in ("A", "B", "C"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")

    class ValidateContext(pyblish.api.Validator):
        families = ["myFamily"]
        def process(self, context):
            count["#"] += 1

    context = pyblish.api.Context()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectMany, ValidateContext],
            context=context):
        pass

    assert_equals(count["#"], 1)


@with_setup(lib.setup_empty, lib.teardown)
def test_incompatible_context():
    """Context is processed regardless of families"""

    count = {"#": 0}

    class SelectMany(pyblish.api.Selector):
        def process(self, context):
            for name in ("A", "B", "C"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")

    class ValidateContext(pyblish.api.Validator):
        def process(self, context):
            count["#"] += 1

    context = pyblish.api.Context()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectMany, ValidateContext],
            context=context):
        pass

    assert_equals(count["#"], 1)

    count["#"] = 0

    # When families are wildcard, it does process
    class ValidateContext(pyblish.api.Validator):
        families = ["NOT_EXIST"]
        def process(self, context):
            count["#"] += 1

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectMany, ValidateContext],
            context=context):
        pass

    assert_equals(count["#"], 0)


def test_custom_test():
    """Registering a custom test works fine"""


def test_logic_process():
    """logic.process works fine"""
    
    context = pyblish.api.Context()
    provider = pyblish.plugin.Provider()
    provider.inject("context", context)

    def my_process(plugin, context, instance=None):
      result = {
        "success": False,
        "plugin": plugin,
        "instance": None,
        "error": None,
        "records": list(),
        "duration": None
      }
      plugin = plugin()
      provider = pyblish.plugin.Provider()
      provider.inject("context", context)
      provider.invoke(plugin.process)
      return result
    
    class SelectInstance(pyblish.api.Selector):
      def process(self, context):
        context.create_instance("MyInstance")
    
    for result in pyblish.logic.process(
            plugins=[SelectInstance],
            func=my_process,
            context=context):
        assert not isinstance(result, pyblish.logic.TestFailed), result
    
    assert_equals(len(context), 1)

@with_setup(lib.setup_empty, lib.teardown)
def test_active():
    """An inactive plug-in won't be processed by default logic"""

    count = {"#": 0}

    class SelectInstances4321(pyblish.api.Selector):
        def process(self, context):
            for name in ("A", "B"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")

            count["#"] += 1

    class ValidateNotActive(pyblish.api.Validator):
        """Doesn't run, due to being inactive"""
        active = False

        def process(self, instance):
            count["#"] += 10
            assert False

    class ValidateActive(pyblish.api.Validator):
        """Runs twice, for both instances"""
        active = True

        def process(self, instance):
            count["#"] += 100

    context = pyblish.api.Context()
    for result in pyblish.logic.process(
            plugins=[SelectInstances4321,
                     ValidateNotActive,
                     ValidateActive],
            func=pyblish.plugin.process,
            context=context):
        assert not isinstance(result, pyblish.logic.TestFailed), result

    assert_equals(count["#"], 201)
