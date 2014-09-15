.. _reference:

Reference
=========

Most of what Pyblish provides can be found in the :mod:`pyblish.backend.plugin` module. In it are two central objects - Context and Instance - along with four processors - Selector, Validator, Extractor and Conformer.

The context is singular throughout the lifespan of a single publish and contains instances. An instance represents what may ultimately become one or more files on disk, such as a model or pointcache. A context then contains one or more of these, as governed by the contents of your current working file.

The :mod:`main` module contains convenience functions, such as :mod:`main.select` that encapsulate multiple commands, such as :mod:`pyblish.backend.plugin.Context()` and :mod:`pyblish.backend.plugin.discover()`.


.. toctree::
    :maxdepth: 1
    
    main
    plugin
    config