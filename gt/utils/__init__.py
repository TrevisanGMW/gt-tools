"""
 Utilities
 github.com/TrevisanGMW - 2020-09-13

 TODO:
     Ideas:
        Assign lambert to everything function (Maybe assign to object missing shaders)
        Add Unlock all attributes
        Add unhide attributes
        Add Remove pasted_ function
        Add assign checkerboard function (already in bonus tools > rendering)
        Force focus (focus without looking at children)
        Brute force clean models (export OBJ and reimport)
"""
import sys
import os

# Paths to Append
source_dir = os.path.dirname(__file__)
package_dir = os.path.dirname(source_dir)
parent_dir = os.path.dirname(package_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
