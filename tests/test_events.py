from pyblish import api, util
from nose.tools import (
    with_setup,
)
from . import lib


@with_setup(lib.setup_empty)
def test_published_event():
    """published is emitted upon finished publish"""

    count = {"#": 0}

    def on_published(context):
        assert isinstance(context, api.Context)
        count["#"] += 1

    api.register_callback("published", on_published)
    util.publish()

    assert count["#"] == 1, count


@with_setup(lib.setup_empty)
def test_validated_event():
    """validated is emitted upon finished validation"""

    count = {"#": 0}

    def on_validated(context):
        assert isinstance(context, api.Context)
        count["#"] += 1

    api.register_callback("validated", on_validated)
    util.validate()

    assert count["#"] == 1, count


@with_setup(lib.setup_empty)
def test_plugin_processed_event():
    """pluginProcessed is emitted upon a plugin being processed

    Regardless of its success.

    """

    class MyContextCollector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            context.create_instance("A")

    class CheckInstancePass(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            pass

    class CheckInstanceFail(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            raise Exception("Test Fail")

    api.register_plugin(MyContextCollector)
    api.register_plugin(CheckInstancePass)
    api.register_plugin(CheckInstanceFail)

    count = {"#": 0}

    def on_processed(result):
        assert isinstance(result, dict)
        count["#"] += 1

    api.register_callback("pluginProcessed", on_processed)
    util.publish()

    assert count["#"] == 3, count


@with_setup(lib.setup_empty)
def test_plugin_failed_event():
    """pluginFailed is emitted upon a plugin failing for any reason"""

    class MyContextCollector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            context.create_instance("A")

    class CheckInstancePass(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            pass

    class CheckInstanceFail(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            raise Exception("Test Fail")

    api.register_plugin(MyContextCollector)
    api.register_plugin(CheckInstancePass)
    api.register_plugin(CheckInstanceFail)

    count = {"#": 0}

    def on_failed(plugin, context, instance, error):
        assert issubclass(plugin, api.InstancePlugin)
        assert isinstance(context, api.Context)
        assert isinstance(instance, api.Instance)
        assert isinstance(error, Exception)

        count["#"] += 1

    api.register_callback("pluginFailed", on_failed)
    util.publish()

    assert count["#"] == 1, count
