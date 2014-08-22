# Standard library
import os
import json

# Local library
import publish
import publish.tests
import publish.config


class TestRegisterValidators(publish.tests.BaseTestCase):
    def test_default_config(self):
        """Ensure default config is JSON and reads well"""

        with open(publish.config.DEFAULTCONFIGPATH, 'r') as f:
            manual_config = json.load(f)

        for key, value in manual_config.iteritems():
            self.assertEquals(value, getattr(publish.config, key))

    def test_user_config(self):
        """A user-config should always be present"""

        self.assertTrue(
            os.path.isfile(
                publish.config.USERCONFIGPATH))
