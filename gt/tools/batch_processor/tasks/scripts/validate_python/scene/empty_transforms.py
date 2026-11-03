# Warns about empty transforms (no children and no shapes), which are often
# leftovers from cleanup steps. Default cameras are ignored.

IGNORED_NAMES = set(["persp", "top", "front", "side"])

transforms = cmds.ls(type="transform", long=True) or []
for transform_path in transforms:
    short_name = transform_path.split("|")[-1]
    if short_name in IGNORED_NAMES or cmds.nodeType(transform_path) != "transform":
        continue
    if not cmds.listRelatives(transform_path, children=True):
        validation.warning("Empty transform.", node=transform_path)
