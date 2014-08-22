# Standard library
import os
import shutil
import tempfile

# Local library
import publish
import publish.tests
import publish.plugin
import publish.config


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
                               'ValidateBlank2',
                               'ValidateNamingConvention']

        # List available validators
        plugins = publish.plugin.discover(type='validators')

        for plugin in plugins:
            validator_name = plugin.__name__
            self.assertIn(validator_name, expected_validators)

    def test_regex(self):
        """Return only plugins matching the regex

        Existing plugins:
            - ValidateBlank1
            - ValidateBlank2
            - ...

        """

        plugins = publish.plugin.discover('validators', regex='.*Blank1')
        plugin_names = [plugin.__name__ for plugin in plugins]
        self.assertIn('ValidateBlank1', plugin_names)
        self.assertNotIn('ValidateBlank2', plugin_names)

    def test_environment_variable(self):
        """Plugin is discovered when located on env path"""

        try:
            # Make a new path, and add a new plugin there.
            plugin_path = tempfile.mkdtemp()
            plugin_module = os.path.join(plugin_path, 'validate_test.py')

            with open(plugin_module, 'w') as f:
                f.write("""
import publish.abstract
class ValidateTest(publish.abstract.Validator):
    pass
    """)

            self.assertTrue(os.path.exists(plugin_module))

            env_var = publish.config.paths_environment_variable
            os.environ[env_var] = plugin_path

            plugins = list()
            for plugin in publish.plugin.discover('validators'):
                plugins.append(plugin.__name__)

            self.assertIn('ValidateTest', plugins)

            # Restore environment
            os.environ.pop(env_var)

        finally:
            shutil.rmtree(plugin_path)


if __name__ == '__main__':
    import unittest
    unittest.main()
