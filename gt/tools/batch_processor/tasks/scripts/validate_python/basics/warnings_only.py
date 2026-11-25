# Reports a warning but no errors.
# - "Warnings Are Issues" on: the file counts as having issues
#   (logged with "Log Issues Only", fails the task with "Fail On Issues").
# - "Warnings Are Issues" off: the file passes and the warning is only logged
#   when "Log Mode" is "Log All".

validation.warning("This scene has something worth reviewing, but it is not an error.")
validation.info("Info messages are kept in the log but never count as issues.")
