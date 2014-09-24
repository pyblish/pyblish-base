import pyblish


@pyblish.log
class SelectDuplicateInstance(pyblish.Selector):
    hosts = ['python']
    version = (0, 1, 0)
