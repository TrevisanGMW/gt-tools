# Fails when any required transform is missing from the scene.
# Edit REQUIRED_TRANSFORMS for your project. Use full paths to require a
# specific hierarchy, or short names to accept the node anywhere.

REQUIRED_TRANSFORMS = [
    "root",
    "geometry_grp",
]

for transform_name in REQUIRED_TRANSFORMS:
    matches = cmds.ls(transform_name, type="transform", long=True) or []
    if validation.check(matches, f"Missing required transform: {transform_name}", node=transform_name):
        if len(matches) > 1:
            validation.warning(
                f"Transform name is not unique ({len(matches)} matches): {transform_name}",
                node=transform_name,
                matches=matches,
            )
