# Standard library
import os

# Local library
import publish
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
        package_dir = os.path.dirname(publish.__file__)
        validators_path = os.path.join(package_dir, 'test_directory')
        validators_path = os.path.abspath(validators_path)

        publish.plugin.register_plugin_path(validators_path)
        self.assertIn(validators_path, publish.plugin.registered)

        publish.plugin.deregister_plugin_path(validators_path)
        self.assertNotIn(validators_path, publish.plugin.registered)

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
        plugins = publish.plugin.discover(type='validators')

        for plugin in plugins:
            validator_name = plugin.__name__
            self.assertIn(validator_name, expected_validators)


if __name__ == '__main__':
    import unittest
    unittest.main()
