import pyblish.api


@pyblish.api.log
class SelectDuplicateInstance(pyblish.api.Selector):
    hosts = ['python']
    version = (0, 1, 0)
