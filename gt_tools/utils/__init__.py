import os
import sys

# Paths to Append (utils, gt_tools)
_this_folder = os.path.dirname(__file__)
_parent_folder = os.path.dirname(_this_folder)

for to_append in [_this_folder, _parent_folder]:
    if to_append not in sys.path:
        sys.path.append(to_append)
