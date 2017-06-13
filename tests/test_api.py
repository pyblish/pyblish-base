import os

import pyblish.api


def test_environment_host_registration():
    """Host registration from PYBLISH_HOSTS works"""

    # Test single host
    pyblish.api.deregister_all_hosts()
    os.environ["PYBLISH_HOSTS"] = "test"

    pyblish.api.__init__()

    registered_hosts = pyblish.api.registered_hosts()
    msg = "Registered hosts: {0}"
    assert "test" in registered_hosts, msg.format(registered_hosts)

    # Test multiple hosts
    pyblish.api.deregister_all_hosts()
    os.environ["PYBLISH_HOSTS"] = os.pathsep.join(["test1", "test2"])

    pyblish.api.__init__()

    registered_hosts = pyblish.api.registered_hosts()
    msg = "Registered hosts: {0}"
    assert "test1" in registered_hosts, msg.format(registered_hosts)
    assert "test2" in registered_hosts, msg.format(registered_hosts)
