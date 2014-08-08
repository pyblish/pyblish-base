"""Persistent settings"""

import os
import sys
import json

import publish

_package_dir = os.path.dirname(publish.__file__)
_config_path = os.path.join(_package_dir, 'config.json')
with open(_config_path, 'r') as f:
    config = type('Config', (object,), json.load(f))

sys.modules[__name__] = config
