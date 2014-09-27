
import pyblish.main
import pyblish.plugin

from pyblish.vendor import mock
from pyblish.vendor.nose.tools import with_setup
from pyblish.tests.lib import (
    setup, teardown, FAMILY, HOST, setup_failing, setup_full)


@with_setup(setup_full, teardown)
def test_publish_all():
    """publish() calls upon each convenience function"""
    ctx = pyblish.plugin.Context()
    pyblish.main.publish(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.main.log')
def test_publish_all_no_instances(mock_log):
    ctx = pyblish.plugin.Context()
    pyblish.main.publish(ctx)
    assert mock_log.warning.called


@with_setup(setup_full, teardown)
def test_publish_all_no_context():
    ctx = pyblish.main.publish()

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@with_setup(setup_full, teardown)
def test_validate_all():
    """validate_all() calls upon two of the convenience functions"""
    ctx = pyblish.plugin.Context()
    pyblish.main.validate_all(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False


@with_setup(setup_failing, teardown)
def test_main_safe_processes_fail():
    """Failing selection, extraction or conform merely logs a message"""
    ctx = pyblish.plugin.Context()
    pyblish.main.select(ctx)

    # Give plugins something to process
    inst = ctx.create_instance(name='TestInstance')
    inst.set_data('family', value=FAMILY)
    inst.set_data('host', value=HOST)

    pyblish.main.extract(ctx)
    pyblish.main.conform(ctx)
