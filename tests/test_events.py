import pyblish.api
import pyblish.util
from nose.tools import (
    with_setup,
    assert_raises,
    assert_equals,
)
from . import lib


@with_setup(lib.setup_empty)
def test_published_event():
    """published is emitted upon finished publish"""

    count = {"#": 0}

    def on_published(context):
        assert isinstance(context, pyblish.api.Context)
        count["#"] += 1

    pyblish.api.on("published", on_published)
    pyblish.util.publish()

    assert count["#"] == 1, count


@with_setup(lib.setup_empty)
def test_validated_event():
    """validated is emitted upon finished validation"""

    count = {"#": 0}

    def on_validated(context):
        assert isinstance(context, pyblish.api.Context)
        count["#"] += 1

    pyblish.api.on("validated", on_validated)
    pyblish.util.validate()

    assert count["#"] == 1, count


@with_setup(lib.setup_empty)
def test_plugin_processed_event():
    """pluginProcessed is emitted upon a plugin being processed

    It is emitted regardless of success.

    """

    class MyContextCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("A")

    class CheckInstancePass(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            pass

    class CheckInstanceFail(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            raise Exception("Test Fail")

    pyblish.api.register_plugin(MyContextCollector)
    pyblish.api.register_plugin(CheckInstancePass)
    pyblish.api.register_plugin(CheckInstanceFail)

    count = {"#": 0}

    def on_processed(result):
        assert isinstance(result, dict)
        count["#"] += 1

    pyblish.api.on("pluginProcessed", on_processed)
    pyblish.util.publish()

    assert count["#"] == 3, count


@with_setup(lib.setup_empty)
def test_plugin_failed_event():
    """pluginFailed is emitted upon a plugin failing for any reason"""

    class MyContextCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("A")

    class CheckInstancePass(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            pass

    class CheckInstanceFail(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            raise Exception("Test Fail")

    pyblish.api.register_plugin(MyContextCollector)
    pyblish.api.register_plugin(CheckInstancePass)
    pyblish.api.register_plugin(CheckInstanceFail)

    count = {"#": 0}

    def on_failed(plugin, context, instance, error):
        assert issubclass(plugin, pyblish.api.InstancePlugin)
        assert isinstance(context, pyblish.api.Context)
        assert isinstance(instance, pyblish.api.Instance)
        assert isinstance(error, Exception)

        count["#"] += 1

    pyblish.api.on("pluginFailed", on_failed)
    pyblish.util.publish()

    assert count["#"] == 1, count


@with_setup(lib.setup_empty, lib.teardown)
def test_register_handler():
    """Callback registration/deregistration works well"""

    def my_handler():
        pass

    def other_handler(data=None):
        pass

    pyblish.api.on("mySignal", my_handler)

    assert "mySignal" in pyblish.api.registered_handlers()

    pyblish.api.deregister_handler("mySignal", my_handler)

    # The handler does not exist
    assert_raises(KeyError,
                  pyblish.api.deregister_handler,
                  "mySignal", my_handler)

    # The signal does not exist
    assert_raises(KeyError,
                  pyblish.api.deregister_handler,
                  "notExist", my_handler)

    assert_equals(pyblish.api.registered_handlers(), [])

    pyblish.api.on("mySignal", my_handler)
    pyblish.api.on("otherSignal", other_handler)
    pyblish.api.deregister_all_handlers()

    assert_equals(pyblish.api.registered_handlers(), [])


def test_weak_handler():
    """Callbacks have weak references"""

    count = {"#": 0}

    def my_handler():
        count["#"] += 1

    pyblish.api.on("on_handler", my_handler)
    pyblish.api.emit("on_handler")
    assert count["#"] == 1

    del(my_handler)

    pyblish.api.emit("on_handler")

    # No errors were thrown, count did not increase
    assert count["#"] == 1


@with_setup(lib.setup_empty, lib.teardown)
def test_emit_signal_wrongly():
    """Exception from handler prints traceback"""

    def other_handler(an_argument=None):
        print("Ping from 'other_handler' with %s" % an_argument)

    pyblish.api.on("otherSignal", other_handler)

    with lib.captured_stderr() as stderr:
        pyblish.lib.emit("otherSignal", not_an_argument="")
        output = stderr.getvalue().strip()
        print("Output: %s" % stderr.getvalue())
        assert output.startswith("Traceback")


@with_setup(lib.setup_empty, lib.teardown)
def test_bound_handler():
    """Handlers may be bound to a class"""

    count = {"#": 0}

    class MyObject(object):
        def __init__(self):
            pyblish.api.on("mySignal", self.on_mysignal)

        def on_mysignal(self):
            count["#"] += 1

    obj = MyObject()
    pyblish.api.emit("mySignal")
    assert_equals(count["#"], 1)

    obj  # Avoid usage warning


@with_setup(lib.setup_empty, lib.teardown)
def test_weak_bound_handler():

    count = {"#": 0}

    class MyObject(object):
        def __init__(self):
            pyblish.api.on("mySignal", self.on_mysignal)

        def on_mysignal(self):
            count["#"] += 1

    obj = MyObject()
    pyblish.api.emit("mySignal")
    assert_equals(count["#"], 1)

    del(obj)
    pyblish.api.emit("mySignal")
    assert_equals(count["#"], 1)
