"""This plugin is used to test how discover handles a mismatching host.
note that there is a host in this plugin, but it is not registered by pyblish"""

import pyblish.plugin

@pyblish.api.log
class CollectMissingHosts(pyblish.plugin.Collector):
    hosts = ['not_a_registered_host']
