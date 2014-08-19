"""Bootstrap currently active host"""

import os
import sys
import imp
import publish

integration_path = os.path.dirname(publish.__file__)


def select(*args, **kwargs):
    try:
        if 'maya' in os.path.basename(sys.executable).lower():
            # Bootstrap Maya
            maya_integration_path = os.path.join(integration_path, 'maya')
            maya_selection_impl = os.path.join(maya_integration_path,
                                               'selection.py')

            try:
                selection = imp.load_source('selection', maya_selection_impl)
            except IOError:
                raise

        else:
            raise IOError

    except IOError:
        raise ValueError("Selection not implemented for host: {0}".format(
                         sys.executable))

    return selection.select(*args, **kwargs)
