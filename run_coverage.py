import os
import sys

# Expose Pyblish to PYTHONPATH
path = os.path.dirname(__file__)
sys.path.insert(0, path)

import nose

if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['-c', '.noserc'])
    nose.main(argv=argv)
