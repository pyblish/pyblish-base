import sys
import weakref
import functools

import pyblish.api
import pyblish.engine
from nose.tools import (
    with_setup,
    assert_equals,
)

from .lib import setup_empty

self = sys.modules[__name__]


def setup():
    self.engine = pyblish.engine.create_default()


@with_setup(setup_empty)
def test_collection():
    """collect() works as expected."""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            count["#"] += 1

    def on_collection():
        count["#"] += 10

    pyblish.api.register_plugin(MyCollector)

    self.engine.was_collected.connect(on_collection)

    self.engine.collect()

    count["#"] == 10, count


@with_setup(setup_empty)
def test_publish():
    """publish() works as expected"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            instance = context.create_instance("myInstance")
            instance.data["families"] = ["myFamily"]
            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    class MyExtractor(pyblish.api.InstancePlugin):
        order = pyblish.api.ExtractorOrder

        def process(self, instance):
            count["#"] += 100

    class MyIntegrator(pyblish.api.InstancePlugin):
        order = pyblish.api.IntegratorOrder

        def process(self, instance):
            count["#"] += 1000

    for Plugin in (MyCollector,
                   MyValidator,
                   MyExtractor,
                   MyIntegrator):
        pyblish.api.register_plugin(Plugin)

    def on_published():
        """Emitted once, on completion"""
        count["#"] += 10000

    self.engine.was_published.connect(on_published)

    self.engine.reset()

    assert count["#"] == 0, count

    self.engine.publish()

    assert count["#"] == 11111, count


@with_setup(setup_empty)
def test_signals():
    """Signals are emitted as expected"""

    count = {"#": 0}

    def identity():
        return {
            "was_processed": 0,
            "was_discovered": 0,
            "was_reset": 0,
            "was_collected": 0,
            "was_validated": 0,
            "was_extracted": 0,
            "was_integrated": 0,
            "was_published": 0,
            "was_acted": 0,
            "was_finished": 0,
        }

    emitted = identity()

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    def on_signal(name, *args):
        print("Emitting %s" % name)
        emitted[name] += 1

    pyblish.api.register_plugin(MyCollector)
    pyblish.api.register_plugin(MyValidator)

    _funcs = list()
    for signal in identity():
        func = functools.partial(on_signal, signal)
        getattr(self.engine, signal).connect(func)
        _funcs.append(func)

    # During reset, no plug-ins are run.
    self.engine.reset()

    state = identity()
    state["was_reset"] = 1
    state["was_discovered"] = 1
    assert_equals(emitted, state)
    assert_equals(count["#"], 0)

    # Running up till and including collection
    self.engine.collect()
    state["was_collected"] = 1
    state["was_processed"] = 1
    state["was_finished"] = 1
    assert_equals(emitted, state)
    assert_equals(count["#"], 1)

    # Up till and including validation, collection is *not* re-run.
    self.engine.validate()
    state["was_validated"] = 1
    state["was_processed"] = 2
    state["was_finished"] = 2
    assert_equals(emitted, state)
    assert_equals(count["#"], 11)

    # Finish off publishing; at this point, there are no more plug-ins
    # so count should remain the same.
    self.engine.publish()
    state["was_published"] = 1
    state["was_finished"] = 3
    assert_equals(emitted, state)
    assert_equals(count["#"], 11)

    print("Disconnecting")


def test_engine_isolation():
    """One engine does not interfere with another engine in the same process

    An engine declares signals on a class-level,
    but must not call upon signals declared in an
    individual instance of a class.

    This is managed by the dynamic lookup of declared
    signals at run-time, similar to what bindings of Qt
    does with its signals and in fact exists due to
    compatibility with such bindings.

    """

    engine1 = pyblish.engine.create_default()
    engine2 = pyblish.engine.create_default()

    count = {"#": 0}

    def increment():
        count["#"] += 1

    engine1.was_reset.connect(increment)

    engine2.reset()

    assert count["#"] == 0

    engine1.reset()

    assert count["#"] == 1


def test_signals_to_instancemethod():
    """Signals to instancemethod works well.

    Default Python (2.x) weak references does not support making
    references to methods to an instance of a class.

    """

    count = {"#": 0}

    class MyClass(object):
        def __init__(self):
            engine = pyblish.engine.create_default()
            engine.was_reset.connect(self.func)

            # Synchronous
            engine.reset()

        def func(self):
            count["#"] += 1

    MyClass()

    assert count["#"] == 1, count


def test_default_signals_are_weakly_referenced():
    """Default signals are weakly referenced"""

    count = {"#": 0}

    class Class(object):
        def method(self):
            count["#"] += 1

    obj = Class()

    signal = pyblish.engine.DefaultSignal(str)
    signal.connect(obj.method)

    assert count["#"] == 0, count
    signal.emit()
    assert count["#"] == 1, count

    del(obj)
    signal.emit()

    # Count does not increase, because the observer is dead
    assert count["#"] == 1, count


@with_setup(setup_empty)
def test_engine_cleanup():
    """Engine cleans itself up on deletion"""

    class MyPlugin(pyblish.api.ContextPlugin):
        def process(self, context):
            context.create_instance("MyInstance")

    pyblish.api.register_plugin(MyPlugin)

    engine = pyblish.engine.create_default()
    engine.reset()
    engine.collect()

    instance = engine.context[0]
    weak_instance = weakref.ref(instance)

    assert weak_instance() is not None

    engine.cleanup()
    print(engine.context)
    print(instance)
    del(instance)

    # TODO(marcus): This should pass
    # assert weak_instance() is None, weak_instance


def test_template_signal():
    """TemplateSignal fulfills basic interface"""

    signal = pyblish.engine.TemplateSignal(str)

    assert len(signal.args) == 1
    assert signal.args[0] == str

    def func():
        pass

    signal.connect(func)
    signal.disconnect(func)
    signal.emit("Hello")


@with_setup(setup_empty)
def test_cvei():
    """CVEI stages trigger plug-in in the appropriate order"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    class MyExtractor(pyblish.api.InstancePlugin):
        order = pyblish.api.ExtractorOrder

        def process(self, instance):
            count["#"] += 100

    class MyIntegrator(pyblish.api.InstancePlugin):
        order = pyblish.api.IntegratorOrder

        def process(self, instance):
            count["#"] += 1000

    for Plugin in (MyCollector,
                   MyValidator,
                   MyExtractor,
                   MyIntegrator):
        pyblish.api.register_plugin(Plugin)

    engine = pyblish.engine.create_default()
    engine.reset()

    assert count["#"] == 0

    engine.collect()

    assert count["#"] == 1

    engine.validate()

    assert count["#"] == 11

    engine.extract()

    assert count["#"] == 111

    engine.integrate()

    assert count["#"] == 1111

    # No more plug-ins to run.
    engine.publish()

    assert count["#"] == 1111


def test_defaultsignal_disconnect():
    """Observers may be disconnected"""

    count = {"#": 0}
    signal = pyblish.engine.DefaultSignal(str)

    def func():
        count["#"] += 1

    signal.connect(func)

    signal.emit()
    assert count["#"] == 1

    signal.disconnect(func)

    signal.emit()
    assert count["#"] == 1
