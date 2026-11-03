# Instead of (or in addition to) the "validation" object, a script can define
# run(context) and return a result:
#   None or True        -> pass (only what was reported through validation counts)
#   False               -> fail with a generic error
#   "message"           -> one error
#   ["msg", {...}]      -> one issue per item; dict items accept severity/message/node
#   {"status": "failed" | "warning" | "passed" | "skipped",
#    "message": "...", "issues": [...]}


def run(context):
    """Returns a list of issues instead of calling the validation object.

    Args:
        context (dict): Batch runtime context.

    Returns:
        list: Issue strings or dictionaries. An empty list means the file passed.
    """
    issues = []
    if context.get("preview"):
        issues.append({"severity": "Info", "message": "Running as a current-scene preview."})
    if not context.get("file_name"):
        issues.append({"severity": "Warning", "message": "No file name (untitled scene?)."})
    return issues
