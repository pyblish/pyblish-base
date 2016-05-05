import pyblish.api
import pyblish.logic
import pyblish.plugin

from nose.tools import (
    assert_equals,
    with_setup
)

from . import lib


@with_setup(lib.setup_empty, lib.teardown)
def test_simple_discover():
    """Simple plug-ins works well with discover()"""

    count = {"#": 0}

    class SimplePlugin(pyblish.api.Plugin):
        def process(self, context):
            self.log.info("Processing context..")
            self.log.info("Done!")
            count["#"] += 1

    class SimplePlugin2(pyblish.api.Validator):
        def process(self, context):
            self.log.info("Processing context..")
            self.log.info("Done!")
            count["#"] += 1

    pyblish.api.register_plugin(SimplePlugin)
    pyblish.api.register_plugin(SimplePlugin2)

    assert_equals(
        list(p.id for p in pyblish.api.discover()),
        list(p.id for p in [SimplePlugin, SimplePlugin2])
    )

    pyblish.util.publish()

    assert_equals(count["#"], 2)


def test_simple_manual():
    """Simple plug-ins work well"""

    count = {"#": 0}

    class SimplePlugin(pyblish.api.Plugin):
        def process(self):
            self.log.info("Processing..")
            self.log.info("Done!")
            count["#"] += 1

    pyblish.util.publish(plugins=[SimplePlugin])

    assert_equals(count["#"], 1)


def test_simple_instance():
    """Simple plug-ins process instances as usual

    But considering they don't have an order, we will have to
    manually enforce an ordering if we are to expect
    them to run one after the other.

    """

    count = {"#": 0}

    class SimpleSelector(pyblish.api.Plugin):
        """Runs once"""
        order = 0

        def process(self, context):
            instance = context.create_instance(name="A")
            instance.set_data("family", "familyA")

            instance = context.create_instance(name="B")
            instance.set_data("family", "familyB")

            count["#"] += 1

    class SimpleValidator(pyblish.api.Plugin):
        """Runs twice"""
        order = 1

        def process(self, instance):
            count["#"] += 10

    class SimpleValidatorForB(pyblish.api.Plugin):
        """Runs once, for familyB"""
        families = ["familyB"]
        order = 2

        def process(self, instance):
            count["#"] += 100

    pyblish.util.publish(plugins=[SimpleSelector,
                                  SimpleValidator,
                                  SimpleValidatorForB])

    assert_equals(count["#"], 121)


def test_simple_order():
    """Simple plug-ins defaults to running *before* SVEC"""

    order = list()

    class SimplePlugin(pyblish.api.Plugin):
        def process(self):
            order.append(1)

    class SelectSomething1234(pyblish.api.Selector):
        def process(self):
            order.append(2)

    class ValidateSomething1234(pyblish.api.Validator):
        def process(self):
            order.append(3)

    class ExtractSomething1234(pyblish.api.Extractor):
        def process(self):
            order.append(4)

    for plugin in (ExtractSomething1234,
                   ValidateSomething1234,
                   SimplePlugin,
                   SelectSomething1234):
        pyblish.api.register_plugin(plugin)

    plugins = pyblish.api.discover()
    context = pyblish.api.Context()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=plugins,
            context=context):
        print(result)

    assert_equals(order, [1, 2, 3, 4])
