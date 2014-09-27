
import os
import sys
import logging

from .version import *
from .vendor import yaml


class Config(dict):
    """Wrapper for config.yaml, user and custom configuration

    .. note:: Config is a singleton.

    Usage:
        >> config = Config()
        >> for key, value in config.iteritems():
        ..     assert key in config

    """

    _instance = None

    DEFAULTCONFIG = "config.yaml"
    USERCONFIG = ".pyblish"
    HOMEDIR = os.path.expanduser('~')
    PACKAGEDIR = os.path.dirname(__file__)
    USERCONFIGPATH = os.path.join(HOMEDIR, USERCONFIG)
    DEFAULTCONFIGPATH = os.path.join(PACKAGEDIR, DEFAULTCONFIG)

    log = logging.getLogger('pyblish.Config')

    default = dict()  # Default configuration data
    user = dict()  # User configuration data

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.reset()

    def reset(self):
        self.clear()

        data = self._load_default()
        data.update(self._load_user())

        for key, value in data.iteritems():
            self[key] = value

    def _load_default(self):
        """Load default configuration from package dir"""

        data = dict()

        # Append to self.default
        data['USERCONFIG'] = self.USERCONFIG
        data['DEFAULTCONFIG'] = self.DEFAULTCONFIG
        data['USERCONFIGPATH'] = self.USERCONFIGPATH
        data['DEFAULTCONFIGPATH'] = self.DEFAULTCONFIGPATH

        with open(self.DEFAULTCONFIGPATH, 'r') as f:
            data.update(yaml.load(f))

        self.default.clear()
        self.default.update(data)

        return data

    def _load_user(self):
        """Load user configuration from HOME directory"""

        data = dict()

        if os.path.isfile(self.USERCONFIGPATH):
            try:
                with open(self.USERCONFIGPATH, 'r') as f:
                    data.update(yaml.load(f))
            except:
                sys.stderr.write("Error: Could not read user configuration "
                                 "@ {0}\n".format(self.USERCONFIGPATH))
                return {}

        self.user.clear()
        self.user.update(data)

        return data
