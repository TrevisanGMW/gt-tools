# Checks that the number of joints in the scene is inside an expected range.
# Useful to catch missing skeletons or duplicated rigs after imports.

MINIMUM_JOINTS = 1
MAXIMUM_JOINTS = 300

joints = cmds.ls(type="joint", long=True) or []
joint_count = len(joints)

validation.check(
    joint_count >= MINIMUM_JOINTS,
    f"Expected at least {MINIMUM_JOINTS} joint(s), found {joint_count}.",
    joint_count=joint_count,
)
validation.check(
    joint_count <= MAXIMUM_JOINTS,
    f"Expected at most {MAXIMUM_JOINTS} joint(s), found {joint_count}.",
    severity="Warning",
    joint_count=joint_count,
)
validation.info(f"Joint count: {joint_count}")
