# Copies the animation score into the Annotation Tracker file-level field.
# The task itself never touches annotation data; this example does it explicitly.
# Enable "Save Scene" in the Score Attribute section (or save here) to keep the change.
#
# Settings:
QUALITY_FIELD = "quality"  # File-level annotation field that receives the 0-100 score.
ONLY_IF_UNSET = True  # Keep existing ratings (empty, "---", and 0 count as unset).

import json
import sys
import maya.cmds as cmds
from gt.tools.anim_annotation_tracker import annotation_tracker_model
from gt.tools.anim_annotation_tracker import annotation_tracker_scene

node_attribute = f"{annotation_tracker_model.SCENE_DATA_NODE_NAME}.{annotation_tracker_model.SCENE_DATA_ATTRIBUTE}"
payload = {"file_data": {}, "range_data": []}
if cmds.objExists(node_attribute):
    payload = json.loads(cmds.getAttr(node_attribute) or "{}") or payload

file_data = dict(payload.get("file_data") or {})
current_value = file_data.get(QUALITY_FIELD)
is_unset = current_value in (None, "", "---", 0, "0")
if ONLY_IF_UNSET and not is_unset:
    sys.stdout.write(f"Kept existing {QUALITY_FIELD} '{current_value}' (score {score}).\n")
else:
    file_data[QUALITY_FIELD] = int(score)
    annotation_tracker_scene.set_scene_annotation_data(file_data, payload.get("range_data") or [])
    sys.stdout.write(f"Set annotation {QUALITY_FIELD} to {score}.\n")
