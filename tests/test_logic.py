
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
            count["#"] += 10
            assert False, "I was programmed to fail"

    class ExtractInstance(pyblish.api.Extractor):
        def process(self, instance):
            count["#"] += 100

    pyblish.api.register_plugin(SelectInstance)
    pyblish.api.register_plugin(ValidateInstance)
    pyblish.api.register_plugin(ExtractInstance)

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=pyblish.plugin.discover(),
            context=pyblish.plugin.Context()):

        if isinstance(result, pyblish.logic.TestFailed):
            break

        if isinstance(result, Exception):
            assert False  # This would be a bug

    assert_equals(count["#"], 11)

    context = pyblish.plugin.Context()

    def _context():
        return context

    count["#"] = 0

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=pyblish.plugin.discover,  # <- Callable
            context=_context):  # <- Callable

        if isinstance(result, pyblish.logic.TestFailed):
            break

        if isinstance(result, Exception):
            assert False  # This would be a bug

    assert_equals(count["#"], 11)


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


@with_setup(lib.setup_empty, lib.teardown)
def test_custom_test():
    """Registering a custom test works fine"""

    count = {"#": 0}

    def custom_test(**vars):
        print "I accept anything"
        return

    class MyValidator(pyblish.api.Validator):
        def process(self, context):
            assert False, "I won't stop the extractor"

    class MyExtractor(pyblish.api.Extractor):
        def process(self, context):
            print "I came, I saw, I extracted.."
            count["#"] += 1

    pyblish.api.register_plugin(MyValidator)
    pyblish.api.register_plugin(MyExtractor)
    pyblish.api.register_test(custom_test)

    pyblish.util.publish()
    assert_equals(count["#"], 1)


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

    for plugin in (SelectInstances4321, ValidateNotActive, ValidateActive):
        pyblish.api.register_plugin(plugin)

    pyblish.util.publish()
    assert_equals(count["#"], 201)


@with_setup(lib.setup_empty, lib.teardown)
def test_failing_selector():
    """Failing Selector should not abort publishing"""

    count = {"#": 0}

    class MySelector(pyblish.api.Selector):
        def process(self, context):
            assert False, "I shouldn't stop Extraction"

    class MyExtractor(pyblish.api.Extractor):
        def process(self):
            count["#"] += 1

    pyblish.api.register_plugin(MySelector)
    pyblish.api.register_plugin(MyExtractor)

    pyblish.util.publish()
    assert_equals(count["#"], 1)


@with_setup(lib.setup_empty, lib.teardown)
def test_decrementing_order():
    """Decrementing order works fine"""

    count = {"#": 0}

    class MyDecrementingSelector(pyblish.api.Selector):
        order = pyblish.api.Selector.order - 0.3

        def process(self):
            count["#"] += 0.1

    class MySelector(pyblish.api.Selector):
        def process(self, context):
            count["#"] += 1
            assert False, "I shouldn't stop Extraction"

    class MyValidator(pyblish.api.Validator):
        order = pyblish.api.Validator.order - 0.4

        def process(self):
            count["#"] += 10
            assert False, "I will run first, and stop things"

    class MyValidator2(pyblish.api.Validator):
        order = pyblish.api.Validator.order + 0.4

        def process(self):
            count["#"] += 100
            assert False, "I will stop things"

    class MyExtractor(pyblish.api.Extractor):
        order = pyblish.api.Extractor.order - 0.49

        def process(self):
            count["#"] += 1000
            assert False, "I will not run"

    class MyExtractor2(pyblish.api.Extractor):
        order = pyblish.api.Extractor.order - 0.2

        def process(self):
            count["#"] += 10000
            assert False, "I will not run"

    for plugin in (
            MyDecrementingSelector,
            MySelector,
            MyValidator,
            MyValidator2,
            MyExtractor):
        pyblish.api.register_plugin(plugin)

    pyblish.util.publish()
    assert_equals(count["#"], 111.1)


def test_extract_traceback():
    e = None

    try:
        1 / 0
    except Exception as e:
        assert not hasattr(e, "traceback")
        pyblish.logic._extract_traceback(e)

    assert hasattr(e, "traceback")
