# Minimal passing validation.
# A Validate Python script passes when it reports no errors (and no warnings,
# while "Warnings Are Issues" is on). Info messages never count as issues.
#
# Report results through the global "validation" object:
#   validation.info(message, node=None, **details)     -> note only, never an issue
#   validation.warning(message, node=None, **details)  -> issue when "Warnings Are Issues" is on
#   validation.error(message, node=None, **details)    -> always an issue (alias: validation.fail)
#   validation.check(condition, message, severity="Error", node=None, **details) -> bool
#   validation.skip(reason)                             -> mark this file as skipped
#
# Other globals: cmds, context, arguments/args, environment_variables/env,
# project, task, work_item, output_path/log_dir, scene_loaded, preview.

validation.info("Nothing to check, this file always passes.")
