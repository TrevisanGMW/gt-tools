# validation.check(condition, message) records a check and reports the message
# only when the condition is false. The log summary shows "N/M check(s) passed".

file_name = context.get("file_name", "")

validation.check(bool(file_name), "The incoming file has no name.")
validation.check(
    not file_name.lower().startswith("temp"),
    f"File name should not start with 'temp': {file_name}",
    severity="Warning",
)
validation.check(" " not in file_name, f"File name should not contain spaces: {file_name}")
