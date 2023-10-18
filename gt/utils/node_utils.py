"""
Node Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.uuid_utils import get_uuid, get_object_from_uuid
from gt.utils.naming_utils import get_short_name
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Node:
    def __init__(self, path):
        if not path or not isinstance(path, str):
            logger.warning(f'Unable to read node. Provided must be a non-empty string.')
            return
        if not cmds.objExists(path):
            logger.warning(f'Unable to read node "{path}" could not be found in the scene.')
            return
        self.uuid = get_uuid(path)

    def get_uuid(self):
        return self.uuid

    def get_long_name(self):
        return get_object_from_uuid(uuid_string=str(self.uuid))

    def get_short_name(self):
        return get_short_name(self.get_long_name())

    def is_dag(self):
        pass  # TODO

    def get_components(self):
        pass  # TODO

    def exists(self):
        return bool(self.get_long_name())

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    a_node = Node(path="pSphere1")
    print(a_node.exists())