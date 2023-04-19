import os
import sys

# Paths to Append
source_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(source_dir)
for to_append in [source_dir, parent_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
