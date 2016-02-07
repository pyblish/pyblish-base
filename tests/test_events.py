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
