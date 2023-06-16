import logging
import sys
import utils
import tools

# Global Vars
PACKAGE_VERSION = "3.0.0"

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_tools")
logger.setLevel(logging.INFO)

# Dependencies
if sys.version_info.major < 3:
    # String formatting for this error should remain compatible to Python 2 to guarantee feedback
    user_version = "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    error = "Incompatible Python Version. Expected to find 3+. Found version: " + user_version + "\n"
    error += "For Python 2, use an older version of GT-Tools before (e.g. 2.0.0)\n"
    sys.stdout.write(error)
    raise ImportError(error)

# Launch Options
try:
    from utils import system_utils
    system_utils.process_launch_options(sys.argv)
except Exception as e:
    sys.stdout.write("Failed to process launch option. Issue: " + str(e))
