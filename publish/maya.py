"""Publish mock-up for Autodesk Maya 2014-2015

A `Selection` contains one or more `Instance` objects. An `Instance`
represents a publishable unit and will result in one or more related
files on disk - e.g. a Maya scene-file or sequence of images.

Interface:
    - SELECTION using objectSet
    - VALIDATION using mock functions, see `_available_validators` below
    - EXTRACTION via File-->Export selection..
    - No CONFORM

Features:
    - PEP08 and Google Docstring formatted
    - Integration with File-menu
    - Changed "class" --> "family" for better readability in code
    - Testing support for multiple publishes from single scene (model + review)
    - Full interface utilised, including `conform` which currently does nothing
    - Validations, per family

Usage:
    1. Add publish/integration to PYTHONPATH, a menu will appear
        in Maya under File-->Publish
    2. Run File-->Publish or
    3. publish.publish()

Attributes:
    _available_validators: Each family contains zero or more validators.
                           These could potentially be split into its own
                           module/package.
    log: Current logger
    IDENTIFIER: Which attribute identifies an objectset as being publishable
    PREFIX: Initial output directory, relative the working file, before conform

"""


from __future__ import absolute_import

import os
import sys
import time
import logging

from maya import mel
from maya import cmds


__all__ = [
    'selection',
    'validate',
    'extract',
    'conform'
]


# Validators categorised by family.
_available_validators = {
    'animRig': [lambda inst: True],
    'animation': [lambda inst: True],
    'model': [lambda inst: True],
    'review': []
}

log = logging.getLogger('publish.maya')
log.setLevel(logging.INFO)

_formatter = logging.Formatter('%(message)s')

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)
log.addHandler(_stream_handler)

IDENTIFIER = 'publishable'
PREFIX = 'published'


class Selection(set):
    """Store selected instances from currently active scene"""


class Instance(object):
    """An individually publishable component within scene

    Examples include rigs, models.

    .. note:: This class isn't meant for use directly.
        See :meth:selection() below.

    Attributes:
        path (str): Absolute path to instance (i.e. objectSet in this case)
        config (dict): Full configuration, as recorded onto objectSet.

    """

    def __repr__(self):
        """E.g. Instance('publish_model_SEL')"""
        return u"%s(%r)" % (type(self).__name__, self.__str__())

    def __str__(self):
        """E.g. 'publish_model_SEL'"""
        return str(self.path)

    def __init__(self, path):
        self.path = path
        self.config = dict()


def select():
    """Parse currently active scene and return selection object.

    The selection includes which nodes to extract along
    with their configuration.

    Returns:
        Selection: Fully qualified selection object.

    """

    selection = Selection()

    for path in cmds.ls("*." + IDENTIFIER,
                        objectsOnly=True,
                        type='objectSet'):
        instance = Instance(path=path)

        attrs = cmds.listAttr(path, userDefined=True)
        for attr in attrs:
            if attr == IDENTIFIER:
                continue

            try:
                value = cmds.getAttr(path + "." + attr)
            except:
                continue

            instance.config[attr] = value

        selection.add(instance)

    return selection


def validate(selection):
    """Validate selection `selection`

    Arguments:
        selection (Selection): Parsed selection

    Returns:
        True is successful, False otherwise

    """

    assert isinstance(selection, Selection)

    failures = list()

    for instance in selection:
        family = instance.config.get('family')

        try:
            validators = _available_validators[family]
        except KeyError:
            exc = Warning("No validators found for family: {0}".format(family))
            failures.append(exc)
        else:
            for validator in validators:
                if not validator(instance):
                    exc = Warning("Validator failed")
                    failures.append(exc)

    return failures


def extract(instance):
    """Physically export data from host

    .. note:: Type of extraction depends on instance family.

    Arguments:
        instance (Instance): Instance from which to export data

    """

    assert isinstance(instance, Instance)

    family = instance.config.get('family')

    if family == 'model':
        return _extract_model(instance)

    if family == 'review':
        return _extract_review(instance)

    if family == 'pointcache':
        return _extract_pointcache(instance)

    if family == 'shader':
        return _extract_shader(instance)

    raise Warning("Unrecognised family: {0}".format(family))


def _extract_model(instance):
    """Export geometry as .mb"""

    date = time.strftime("%Y%m%d_%H%M%S")
    family = instance.config.get('family')

    nodes = cmds.sets(instance.path, query=True)
    workspace_dir = cmds.workspace(rootDirectory=True, query=True)
    if not workspace_dir:
        # Project has not been set. Files will
        # instead end up next to the working file.
        workspace_dir = cmds.workspace(dir=True, query=True)
    published_dir = os.path.join(workspace_dir, PREFIX, family)
    extract_dir = os.path.join(published_dir, date)

    output = os.path.join(extract_dir, date)

    if os.path.exists(output):
        raise ValueError("Destination already exists, make sure to allow "
                         "at least 1 second between publishes.")
    if not os.path.isdir(extract_dir):
        os.makedirs(extract_dir)

    previous_selection = cmds.ls(selection=True)
    cmds.select(nodes, replace=True)
    cmds.file(output, type='mayaBinary', exportSelected=True)

    if previous_selection:
        cmds.select(previous_selection, replace=True)
    else:
        cmds.select(deselect=True)

    return extract_dir


def _extract_review(instance):
    """Create playblast"""


def _extract_pointcache(instance):
    """Export alembic pointcache"""


def _extract_shader(instance):
    """Export shaders as .mb"""


def conform(path):
    log.info("Moving %s to new home" % path)


def publish():
    """Convenience method of the above"""

    # parse selection
    selection = select()

    # validate
    failures = validate(selection)

    # extract
    if not failures:
        for instance in selection:
            path = extract(instance)
            log.info("Extracted {0}".format(path))

            # conform
            conform(path)

    else:
        log.info("There were errors:")
        for failure in failures:
            log.info("\t{0}".format(failure))

    log.info("Successfully published scene")


def append_to_filemenu():
    """Add Publish to file-menu

    As Maya builds its menus upon first being accessed,
    you'll have to use eval_append_to_filemenu() below
    if triggered automatically at startup; such as in
    your userSetup.py

    """

    cmds.menuItem('publishOpeningDivider',
                  divider=True,
                  insertAfter='saveAsOptions',
                  parent='mainFileMenu')
    cmds.menuItem('publishScene',
                  label='Publish',
                  insertAfter='publishOpeningDivider',
                  command=lambda _: publish())
    cmds.menuItem('publishCloseDivider',
                  divider=True,
                  insertAfter='publishScene')
    sys.stdout.write("Success")


def eval_append_to_filemenu():
    """Add Publish to file-menu"""
    mel.eval("evalDeferred buildFileMenu")

    script = """
import publish.maya
publish.maya.append_to_filemenu()
    """

    cmds.evalDeferred(script)
