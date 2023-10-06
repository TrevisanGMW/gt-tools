"""
Auto Rigger Spine Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_framework import Proxy, ModuleGeneric
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
