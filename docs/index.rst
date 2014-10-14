
.. image:: logo_small.png

API documentation for Pyblish v\ |version|.

.. module:: pyblish.plugin

Objects
=======

Central objects used throughout Pyblish.

.. autosummary::
    :nosignatures:

    AbstractEntity
    Context
    Instance
    Plugin
    Selector
    Validator
    Extractor
    Conformer

Functions
=========

Helper utilities.

.. autosummary::
    :nosignatures:

    discover
    plugin_paths
    registered_paths
    configured_paths
    environment_paths
    register_plugin_path
    deregister_plugin_path
    deregister_all
    plugins_by_family
    plugins_by_host
    instances_by_plugin

.. module:: pyblish

Configuration
=============

.. autosummary::
    :nosignatures:

    Config

.. module:: pyblish.lib

Library
=======

.. autosummary::
    :nosignatures:

    log
    format_filename

.. module:: pyblish.error

Exceptions
==========

Exceptions raised that are specific to Pyblish.

.. autosummary::
    :nosignatures:

    PyblishError
    SelectionError
    ValidationError
    ExtractionError
    ConformError 

.. module:: pyblish.plugin


AbstractEntity
--------------

Superclass to Context and Instance, providing the data plug-in to plug-in
API via the data member.

.. autoclass:: AbstractEntity
    :members:
    :undoc-members:

Context
-------

The context is a container of one or more objects of type :class:`Instance` along with metadata to describe them all; such as the current working directory or logged on user.

.. autoclass:: Context
    :members:
    :undoc-members:

Instance
--------

An instance describes one or more items in a working scene; you can think of it as the counter-part of a file on disk - once the file has been loaded, it's an `instance`.

.. autoclass:: Instance
    :members:
    :undoc-members:


Plugin
------

As a plug-in driven framework, any action is implemented as a plug-in and this is the superclass from which all plug-ins are derived. The superclass defines behaviour common across all plug-ins, such as its internally executed method :meth:`Plugin.process` or it's virtual members :meth:`Plugin.process_instance` and :meth:`Plugin.process_context`.

Each plug-in MAY define one or more of the following attributes prior to being useful to Pyblish.

- :attr:`Plugin.hosts`
- :attr:`Plugin.optional`
- :attr:`Plugin.version`

Some of which are MANDATORY, others which are OPTIONAL. See each corresponding subclass for details.

- :class:`Selector`
- :class:`Validator`
- :class:`Extractor`
- :class:`Conformer`


.. autoclass:: Plugin
    :members:
    :undoc-members:

Selector
--------

A selector finds instances within a working file.

.. note:: The following attributes must be present when implementing this plug-in.

    - :attr:`Selector.hosts`
    - :attr:`Selector.version`

.. autoclass:: Selector
    :members:
    :undoc-members:

Validator
---------

A validator validates selected instances.

.. note:: The following attributes must be present when implementing this plug-in.

    - :attr:`Plugin.hosts`
    - :attr:`Plugin.version`
    - :attr:`Validator.families`

.. autoclass:: Validator
    :members:
    :undoc-members:

Extractor
---------

Extractors are responsible for serialising selected data into a format suited for persistence on disk. Keep in mind that although an extractor does place file on disk, it isn't responsible for the final destination of files. See :class:`Conformer` for more information.

.. note:: The following attributes must be present when implementing this plug-in.

    - :attr:`Plugin.hosts`
    - :attr:`Plugin.version`
    - :attr:`Extractor.families`

.. autoclass:: Extractor
    :members:
    :undoc-members:

Conformer
---------

The conformer, also known as `integrator`, integrates data produced by extraction.

Its responsibilities include:

1. Placing files into their final destination
2. To manage and increment versions, typically involving a third-party versioning library.
3. To notify artists of events
4. To provide hooks for out-of-band processes

.. note:: The following attributes must be present when implementing this plug-in.

    - :attr:`Plugin.hosts`
    - :attr:`Plugin.version`
    - :attr:`Conformer.families`

.. autoclass:: Conformer
    :members:
    :undoc-members:


discover
--------

.. autofunction:: discover

plugin_paths
------------

.. autofunction:: plugin_paths

registered_paths
----------------

.. autofunction:: registered_paths

configured_paths
----------------

.. autofunction:: configured_paths

environment_paths
-----------------

.. autofunction:: environment_paths

register_plugin_path
--------------------

.. autofunction:: register_plugin_path

deregister_plugin_path
----------------------

.. autofunction:: deregister_plugin_path

deregister_all
--------------

.. autofunction:: deregister_all

plugins_by_family
-----------------

.. autofunction:: plugins_by_family

plugins_by_host
----------------

.. autofunction:: plugins_by_host

instances_by_plugin
-------------------

.. autofunction:: instances_by_plugin

.. module:: pyblish

Config
------

.. autoclass:: Config
    :members:

.. module:: pyblish.lib

log
---

.. autofunction:: log


format_filename
---------------

.. autofunction:: format_filename


.. module:: pyblish.error


PyblishError
------------

.. autoclass:: PyblishError
    :members:
    :undoc-members:

SelectionError
--------------------

.. autoclass:: SelectionError
    :members:
    :undoc-members:

ValidationError
---------------

.. autoclass:: ValidationError
    :members:
    :undoc-members:

ExtractionError
---------------

.. autoclass:: ExtractionError
    :members:
    :undoc-members:

ConformError
------------

.. autoclass:: ConformError
    :members:
    :undoc-members:
