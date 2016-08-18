import pyblish.api
import pyblish.util
from nose.tools import (
    with_setup,
)
from . import lib


@with_setup(lib.setup_empty)
def test_published_event():
    """published is emitted upon finished publish"""

    count = {"#": 0}

    def on_published(context):
        assert isinstance(context, pyblish.api.Context)
        count["#"] += 1

    pyblish.api.register_callback("published", on_published)
    pyblish.util.publish()

    assert count["#"] == 1, count


@with_setup(lib.setup_empty)
def test_validated_event():
    """validated is emitted upon finished validation"""

    count = {"#": 0}

    def on_validated(context):
        assert isinstance(context, pyblish.api.Context)
        count["#"] += 1

    pyblish.api.register_callback("validated", on_validated)
    pyblish.util.validate()

    assert count["#"] == 1, count

@with_setup(lib.setup_empty)
def test_plugin_processed_event():
    """pluginProcessed is emitted upon a plugin being processed, regardless of its success"""

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

    pyblish.api.register_callback("pluginProcessed", on_processed)
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
        assert issubclass(plugin, pyblish.api.InstancePlugin) #plugin == CheckInstanceFail
        assert isinstance(context, pyblish.api.Context)
        assert isinstance(instance, pyblish.api.Instance)
        assert isinstance(error, Exception)

        count["#"] += 1

    pyblish.api.register_callback("pluginFailed", on_failed)
    pyblish.util.publish()

    assert count["#"] == 1, count