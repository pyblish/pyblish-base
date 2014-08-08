# Standard library
import os

# Local library
import publish.tests
import publish.plugin


class TestRegisterValidators(publish.tests.BaseTestCase):
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
                'model': [ValidateMutedChannels,
                          ValidateUniqueNames],
                'pointcache': [ValidateBlank2]
            }

        """

        expected_validators = ['ValidateMutedChannels',
                               'ValidateUniqueNames',
                               'ValidateBlank1',
                               'ValidateBlank2']

        # List available validators
        plugins = publish.plugin.discover_validators()

        for plugin in plugins:
            validator_name = plugin.__name__
            self.assertIn(validator_name, expected_validators)


if __name__ == '__main__':
    import unittest
    unittest.main()
