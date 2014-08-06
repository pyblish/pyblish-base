"""Publish mock-up for Autodesk Maya 2014-2015

A `Context` defines a set of data that can be used to direct and instruct an Action how to operate and/or on what to
operate.

An `Action` performs a functionality within/upon a Context and returns the result of that process.
Even though an `Action` always operates upon a `Context` in some cases the `Context` does not have to be clearly
defined. As in, it doesn't require to contain any data (except for the object Context object to be instantiated).

By our current schema this is the proposed workflow:
1. A `Selector` creates/alters the Context.
2. A `Validator` validates the Context.
3. An `Extractor` assumes the Context and the data it points to is valid and uses the information to Extra a new
   `Resource`.

A `Resource` could be anything that is created as new (outside of the scope of the Context). In theory it could create
a single or multiple file on disk, assign a value to a database and/or import data into the application. In practice
it's primary focus is on writing to a file format on disk.

Because of the above workflow a `Selector` seems to be the only type that could possibly operate without any defined
Context, because it creates/alters it. Yet at this point no checks are made whether the different Action types stay
true to this schema. Currently it is possible to write an Action that simply exports a whole scene another file format
without performing any validation and/or context selection.

Features:
    - Testing "__inputs__" and "__outputs__" for Actions.
    - Modular workflow
    - Remove integration in menu as it didn't appear useful to have a single test button for this modular workflow.

Usage:
    - ***
    Currently still a work in progress and contains no working example.
    Nevertheless it already shows a clear overview of the schema.

Attributes:
    _available_actions: A dictionary mapping of all Actions by Action type according to the proposed schema.
    log: Current logger

"""


from __future__ import absolute_import

import os
import sys
import time
import logging

import publish.core

log = logging.getLogger('publish.maya')
log.setLevel(logging.INFO)

_formatter = logging.Formatter('%(message)s')

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)
log.addHandler(_stream_handler)


# =======
# Context
# =======
class MayaContext(publish.core.Context):
    def __init__(self):
        # TODO: Define whether predefining Context attributes is the way to go.
        # TODO: Discuss what other ways to keep this dynamic/modular yet SAFE and consistent!
        # Pros:
        # 1. It'll give you autocomplete
        # 2. Know what to expect.
        # 3. Can add checks ensuring the data stays in the correct format (properties and setters)
        # 4. Having a single Context define it sets an 'industry standard' for how it should be formatted.
        #    This ensure compatibility between Actions designed by others.
        # Cons:
        # 1. Hard to design for all possibilities of the context.
        # 2. Custom methods for the Context won't be available using Publish within another Context Family and may come
        #    over as confusing.
        self.nodes = set()
        self.range = [0, 0]


# =======
# Actions
# =======
# Selectors: nodes
# ----------------
class MayaNodesSelector(publish.core.Selector):
    __context__ = MayaContext
    __outputs__ = ["nodes"]


class MayaCurrentSelectionSelector(MayaNodesSelector):
    """ Adds the current selection to Context.nodes """
    def process(self, context):
        import maya.cmds as mc
        selection = mc.ls(sl=1, long=True)
        context.nodes.update(selection)
        return context


class MayaMeshSelector(MayaNodesSelector):
    """ Adds all mesh shape nodes to Context.nodes """
    def process(self, context):
        import maya.cmds as mc
        selection = mc.ls(type="mesh", long=True)
        context.nodes.update(selection)
        return context


# Selectors: timerange
# ----------------------
class MayaTimeRangeSelector(publish.core.Selector):
    __context__ = MayaContext
    __outputs__ = ["timerange"]


class MayaSceneAnimationRangeSelector(MayaTimeRangeSelector):
    """ Gets the time range based on all animation in the scene. """
    def process(self, context):
        import maya.cmds as mc
        anim_curves = mc.ls(type="animCurve")
        times = mc.keyframe(anim_curves, q=1, tc=1)
        start = min(times)
        end = max(times)
        context.timerange = [start, end]

        return context


class MayaNodesAnimationRangeSelector(MayaTimeRangeSelector):
    """ Gets the used time range based on animation off the nodes already in the Context. """
    __inputs__ = ["nodes"]

    def process(self, context):
        import maya.cmds as mc
        nodes = context.nodes
        times = mc.keyframe(nodes, q=1, tc=1)
        start = min(times)
        end = max(times)
        context.timerange = [start, end]
        return context


class MayaLimitTimeRangeSelector(MayaTimeRangeSelector):
    """ Clamps the Context's current timerange between (-1000, 1000) """
    __inputs__ = ["timerange"]

    def process(self, context):
        timerange = context.timerange
        if timerange[0] < -1000:
            timerange[0] = -1000
        if timerange[1] > 1000:
            timerange[1] = 1000
        context.timerange = timerange
        return context


class MayaLimitTimeRangeSelector(MayaTimeRangeSelector):
    """ Extends the time range with -10, 10. This could emulate automatically adding handles to your exports """
    __context__ = MayaContext
    __inputs__ = ["timerange"]
    __outputs__ = ["timerange"]

    def process(self, context):
        context.timerange[0] -= 10
        context.timerange[1] += 10
        return context


# Validators: Random
# ------------------
class MayaMinimumTenNodesValidator(publish.core.Validator):
    __context__ = MayaContext
    __inputs__ = ["nodes"]

    def process(self, context):
        nodes = context.nodes
        if len(nodes) >= 10:
            return 1
        else:
            return 0



# Extractors: Random
# ------------------
class MayaExportNodesExtractor(publish.core.Extractor):
    __context__ = MayaContext
    __inputs__ = ["nodes"]

    def process(self, context):
        import maya.cmds as mc
        nodes = context.nodes
        mc.select(nodes, r=1) # select so we can quickly do export selection
        mc.file(es=True, pr=True, type="mayaBinary") # untested, consider as pseudocode


# =================
# Set up 'plug-ins'
# =================
# This is just for testing purposes
_available_actions = {
    "select": [MayaCurrentSelectionSelector, MayaLimitTimeRangeSelector, MayaNodesAnimationRangeSelector,
                 MayaSceneAnimationRangeSelector, MayaTimeRangeSelector],
    "validate": [MayaMinimumTenNodesValidator],
    "extract": [MayaExportNodesExtractor],
    "conform": []
}
