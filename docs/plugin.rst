
Plugins
=======

.. module:: pyblish.backend.plugin

.. autosummary::
   :nosignatures:

   Context
   Instance
   Plugin
   Selector
   Validator
   Extractor
   Conformer
   discover

.. autofunction:: pyblish.backend.plugin.discover
.. autofunction:: pyblish.backend.plugin.plugin_paths

.. autofunction:: pyblish.backend.plugin.register_plugin_path
.. autofunction:: pyblish.backend.plugin.deregister_plugin_path
.. autofunction:: pyblish.backend.plugin.deregister_all

.. autoclass:: pyblish.backend.plugin.AbstractEntity
    :members:
.. autoclass:: pyblish.backend.plugin.Context
    :members:
.. autoclass:: pyblish.backend.plugin.Instance
    :members:

.. autoclass:: pyblish.backend.plugin.Plugin
    :members:
.. autoclass:: pyblish.backend.plugin.Selector
    :members:
.. autoclass:: pyblish.backend.plugin.Validator
    :members:
.. autoclass:: pyblish.backend.plugin.Extractor
    :members:
.. autoclass:: pyblish.backend.plugin.Conformer
    :members:

.. autofunction:: pyblish.backend.plugin.plugins_by_family
.. autofunction:: pyblish.backend.plugin.plugins_by_host
.. autofunction:: pyblish.backend.plugin.instances_by_plugin


.. _`guide`: http://pyblish.com/#configuring-pyblish