import sys
import tools
import utils

# Global Vars
PACKAGE_VERSION = "3.0.0"

# Dependencies
if sys.version_info.major < 3:
    # String formatting for this error should remain compatible to Python 2 to guarantee feedback
    user_version = str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro)
    error = "Incompatible Python Version. Expected to find 3+. Found version: " + user_version + "\n"
    error += "For Python 2, use previous major version of GT-Tools (e.g 2.0.0+)\n"
    sys.stdout.write(error)
    raise ImportError(error)

# Launch Options
try:
    from utils import system_utils
    system_utils.process_launch_options(sys.argv)
except Exception as e:
    sys.stdout.write("Failed to process launch option. Issue: " + str(e))
