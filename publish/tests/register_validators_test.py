#!mayapy

# Standard library
import os

# Local library
import publish.plugin
import publish.tests


class TestRegisterValidators(publish.tests.DefaultTestCase):
    def test_register_validators(self):
        """Paths of where validators may reside are stored in plugin-module

        Users are expected to augment validators by appending
        directories onto a globally accessible list of paths;
        similar to how OS'es look for executables, and how
        nosetest looks for tests.

        """

        # There are included validators with this package
        module_dir = os.path.dirname(__file__)
        validators_path = os.path.join(module_dir, '..', 'test_directory')
        validators_path = os.path.abspath(validators_path)

        publish.plugin.register_plugin_path(validators_path)

        self.assertEquals(publish.plugin.validator_dirs[-1],
                          validators_path)

        publish.plugin.deregister_plugin_path(validators_path)

        self.assertNotEquals(publish.plugin.validator_dirs[-1],
                             validators_path)

    def test_list_validators(self):
        """Validator objects are returned by which family they belong

        Example:
            {
                'model': [Validator('muted_channels_validator'),
                          Validator('unique_names_validator')],
                'pointcache': [Validator('blank2_validator')]
            }

        """

        expected_families = ['model', 'animation', 'animRig', 'pointcache']

        # List available validators
        plugins = publish.plugin.collect_validators()

        families = plugins.keys()
        for family in families:
            self.assertIn(family, expected_families)

        expected_validators = ['muted_channels_validator',
                               'unique_names_validator']

        validators = plugins['model']
        for validator in validators:
            validator_name = str(validator)
            self.assertIn(validator_name, expected_validators)


if __name__ == '__main__':
    import unittest
    unittest.main()
