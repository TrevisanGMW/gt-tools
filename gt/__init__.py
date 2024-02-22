import sys

# Package Variables
__version_tuple__ = (3, 3, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__
__authors__ = ['Guilherme Trevisan']

# Python Version Dependency
if sys.version_info.major < 3:
    # String formatting for this error should remain compatible to Python 2 to guarantee feedback
    user_version = "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    error = "Incompatible Python Version. Expected to find 3+. Found version: " + user_version + "\n"
    error += "For Python 2, use an older version of GT-Tools before 3.0.0 - (e.g. 2.5.5)\n"
    sys.stdout.write(error)
    raise ImportError(error)
