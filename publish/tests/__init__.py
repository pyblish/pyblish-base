
# Standard library
import os
import unittest

import publish.plugin


class DefaultTestCase(unittest.TestCase):
        def setUp(self):
            """Include basic validations"""

            module_dir = os.path.dirname(__file__)
            validators_path = os.path.join(module_dir, '..', 'validators')
            validators_path = os.path.abspath(validators_path)

            publish.plugin.register_plugin_path(validators_path)

        def tearDown(self):
            pass
