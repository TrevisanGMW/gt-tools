"""
Transform Utilities
"""
from dataclasses import dataclass
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("transform_utils")
logger.setLevel(logging.INFO)


@dataclass
class Vector3:
    x: float
    y: float
    z: float


@dataclass
class Transform:
    location: Vector3
    rotation: Vector3
    scale: Vector3


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
