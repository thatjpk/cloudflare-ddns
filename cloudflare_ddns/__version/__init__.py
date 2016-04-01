from codecs import open
import os

__version_py = os.path.join(os.path.dirname(__file__), '__version.py')

if os.path.isfile(__version_py):
    from __version import VERSION
else:
    VERSION = 'dev'

