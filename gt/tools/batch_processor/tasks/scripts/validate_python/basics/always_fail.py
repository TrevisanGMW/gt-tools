# Always fails, so you can see how a failed validation looks in the tracker,
# the log (Target Path), and the "Run On Current Scene" results window.
# With "Fail On Issues" on, the task fails. With it off, the task succeeds but
# the issue is still logged and the project validation status is marked failed.

validation.error("This example always reports an error.")
validation.error(
    "Errors can point at a node and carry extra details.",
    node="|example_grp|example_geo",
    expected=1,
    found=0,
)
