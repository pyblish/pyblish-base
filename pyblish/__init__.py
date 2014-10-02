
import os
import logging

from .version import *
from .vendor import yaml


class Config(dict):
    """Wrapper for default-, user- and custom-configuration

    .. note:: Config is a singleton.

    Configuration is cascading in the following order;

    .. code-block:: bash

         _________     ________     ______
        |         |   |        |   |      |
        | Default | + | Custom | + | User |
        |_________|   |________|   |______|

    In which `User` is being added last and thus overwrites any
    previous configuration.

    Attributes:
        DEFAULTCONFIG: Name of default configuration file
        USERCONFIG: Name of user and custom configuration file
        HOMEDIR: Absolute path to user's home directory
        PACKAGEDIR: Absolute path to parent package of Config
        USERCONFIGPATH: Absolute path to user configuration file
        DEFAULTCONFIGPATH: Absolute path to default configuration file

        default: Access to default configuration
        custom: Access to custom configuration
        user: Access to user configuration

    Usage:
        >>> config = Config()
        >>> for key, value in config.iteritems():
        ...     assert key in config

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
    custom = dict()  # Custom configuration data
    user = dict()  # User configuration data

    def __new__(cls, *args, **kwargs):
        """Make Config into a singleton"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Read all configuration upon instantiation"""
        self.reset()

    def reset(self):
        """Remove all configuration and re-read from disk"""
        self.clear()

        self._load_default()
        self._load_custom()
        self._load_user()

    def load(self, path, data=None):
        """Manually load configuration.

        Arguments:
            path (str): Absolute path to configuration, if
                a directory is specified the file `.pyblish`
                is assumed.
            data (dict): Additional data

        """

        assert data is None or isinstance(data, dict)

        with open(path, 'r') as f:
            loaded_data = yaml.load(f)

        if data is not None:
            loaded_data.update(data)

        for key, value in loaded_data.iteritems():
            self[key] = value

        return loaded_data

    def _load_default(self):
        """Load default configuration from package dir"""

        data = self.load(path=self.DEFAULTCONFIGPATH,
                         data={'USERCONFIG': self.USERCONFIG,
                               'DEFAULTCONFIG': self.DEFAULTCONFIG,
                               'USERCONFIGPATH': self.USERCONFIGPATH,
                               'DEFAULTCONFIGPATH': self.DEFAULTCONFIGPATH})

        # Append to self.default
        self.default.clear()
        self.default.update(data)

        return data

    def _load_user(self):
        """Load user configuration from HOME directory"""

        data = dict()

        if os.path.isfile(self.USERCONFIGPATH):
            try:
                data = self.load(path=self.USERCONFIGPATH)
                print "Loading user: %S" % data
            except Exception:
                self.log.warning("Error: Could not read user configuration "
                                 "@ {0}\n".format(self.USERCONFIGPATH))
                return {}
            else:
                # Do not modify user-data, unless new data
                # was successfully read
                self.user.clear()
                self.user.update(data)

        return data

    def _load_custom(self):
        """Load custom configuration, looking at environment

        .. note:: A note on multiple configuration paths; each
            configuration overrides variables from the last,
            starting from the first available path.

            E.g. if the first configuration defines "my_variable=True"
            and the next "my_variable=False", the final value of
            "my_variable" will be False.

        """

        data = dict()

        variable = self['configuration_environment_variable']
        paths_string = os.environ.get(variable)

        if not paths_string:
            return list()

        sep = ';' if os.name == 'nt' else ':'

        custom_paths = paths_string.split(sep)

        for path in custom_paths:
            try:
                if os.path.isdir(path):
                    path = os.path.join(path, self.USERCONFIG)

                if not os.path.exists(path):
                    raise ValueError

                data.update(self.load(path))

            except Exception:
                self.log.warning("Could not read custom configuration "
                                 "@ {0}\n".format(path))

            else:
                self.log.debug("Loading custom configuration: %s" % path)

        # Store reference
        self.custom = data

        for key, value in data.iteritems():
            self[key] = value
