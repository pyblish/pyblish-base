
import pyblish.util
import pyblish.plugin

from pyblish.vendor import mock
from pyblish.vendor.nose.tools import with_setup
from pyblish.tests.lib import (
    teardown, FAMILY, HOST, setup_failing, setup_full)


@mock.patch('pyblish.util.Publish.log')
@with_setup(setup_full, teardown)
def test_publish_all(_):
    """publish() calls upon each convenience function"""
    ctx = pyblish.plugin.Context()
    pyblish.util.publish(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.util.Publish.log')
def test_publish_all_no_instances(mock_log):
    """Having no instances is fine, a warning is logged"""
    ctx = pyblish.plugin.Context()
    pyblish.util.publish(ctx)
    assert mock_log.warning.called


@with_setup(setup_full, teardown)
def test_publish_all_no_context():
    """Not passing a context is fine"""
    ctx = pyblish.util.publish()

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.util.Publish.log')
@with_setup(setup_full, teardown)
def test_validate_all(_):
    """validate_all() calls upon two of the convenience functions"""
    ctx = pyblish.plugin.Context()
    pyblish.util.validate_all(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False


@mock.patch('pyblish.util.Publish.log')
@with_setup(setup_full, teardown)
def test_convenience(_):
    """Convenience function work"""
    ctx = pyblish.plugin.Context()

    pyblish.util.select(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is False
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False

    pyblish.util.validate(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False

    pyblish.util.extract(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is False

    pyblish.util.conform(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.util.Publish.log')
@with_setup(setup_failing, teardown)
def test_main_safe_processes_fail(_):
    """Failing selection, extraction or conform merely logs a message"""
    ctx = pyblish.plugin.Context()
    pyblish.util.select(ctx)

    # Give plugins something to process
    inst = ctx.create_instance(name='TestInstance')
    inst.set_data('family', value=FAMILY)
    inst.set_data('host', value=HOST)

    pyblish.util.extract(ctx)
    pyblish.util.conform(ctx)
