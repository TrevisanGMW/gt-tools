"""
Batch Processor Command Task Helpers

Pure helpers for the Command task: argument parsing, environment overrides,
exit-code rules, and display formatting. This module never imports Maya or
starts processes, so it stays importable and testable anywhere.
"""

import base64
import os
import re


class CommandMode:
    """How the command text is executed."""

    PROGRAM = "Program"
    SHELL = "Shell"


class ShellType:
    """Shells available to the Shell command mode."""

    SYSTEM = "System Shell"
    POWERSHELL = "PowerShell"


class WaitMode:
    """How the task waits for the started process."""

    WAIT_FOR_EXIT = "Wait For Exit"
    WAIT_UNTIL_READY = "Wait Until Ready"
    LAUNCH_AND_CONTINUE = "Launch And Continue"


class ReadyCheck:
    """Readiness checks used by the Wait Until Ready mode."""

    URL = "URL Responds"
    PORT = "Port Open"
    FILE = "File Exists"
    COMMAND = "Command Succeeds"


class FailureAction:
    """What the task does when the command fails."""

    FAIL = "Fail"
    WARNING = "Warning"
    IGNORE = "Ignore"


COMMAND_MODES = [CommandMode.PROGRAM, CommandMode.SHELL]
SHELL_TYPES = [ShellType.SYSTEM, ShellType.POWERSHELL]
WAIT_MODES = [WaitMode.WAIT_FOR_EXIT, WaitMode.WAIT_UNTIL_READY, WaitMode.LAUNCH_AND_CONTINUE]
READY_CHECKS = [ReadyCheck.URL, ReadyCheck.PORT, ReadyCheck.FILE, ReadyCheck.COMMAND]
FAILURE_ACTIONS = [FailureAction.FAIL, FailureAction.WARNING, FailureAction.IGNORE]

ANY_EXIT_CODE_TOKENS = ("*", "any")
MASKED_VALUE = "********"
_SECRET_KEY_PATTERN = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|PASS|API[_-]?KEY|CREDENTIAL)", re.IGNORECASE)
_ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
_ENVIRONMENT_REFERENCE_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|%([A-Za-z_][A-Za-z0-9_]*)%")


def split_argument_line(line):
    """Splits one line of argument text into arguments.

    Whitespace separates arguments and double quotes group text that contains
    spaces. Backslashes are kept as typed so Windows paths work unchanged.

    Args:
        line (str): One line of argument text.

    Returns:
        list: Parsed arguments without the grouping quotes.
    """
    arguments = []
    current_chars = []
    in_quotes = False
    has_token = False
    for character in str(line or ""):
        if character == '"':
            in_quotes = not in_quotes
            has_token = True
            continue
        if character.isspace() and not in_quotes:
            if has_token:
                arguments.append("".join(current_chars))
            current_chars = []
            has_token = False
            continue
        current_chars.append(character)
        has_token = True
    if has_token:
        arguments.append("".join(current_chars))
    return arguments


def split_arguments(text):
    """Splits multi-line argument text into a flat argument list.

    Lines starting with ``#`` are comments and blank lines are ignored.

    Args:
        text (str or list): Argument text, or an already split list.

    Returns:
        list: Parsed arguments in order.
    """
    if isinstance(text, (list, tuple)):
        return [str(argument) for argument in text]
    arguments = []
    for line in str(text or "").replace("\r\n", "\n").split("\n"):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        arguments.extend(split_argument_line(stripped_line))
    return arguments


def parse_environment_overrides(text):
    """Parses ``KEY=VALUE`` lines into ordered pairs.

    Lines starting with ``#`` are comments. ``KEY=`` sets an empty value.

    Args:
        text (str): Override text, one variable per line.

    Returns:
        tuple: (list of (key, value) pairs, list of error messages).
    """
    pairs = []
    errors = []
    for line_number, line in enumerate(str(text or "").replace("\r\n", "\n").split("\n"), start=1):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        if "=" not in stripped_line:
            errors.append(f'Environment line {line_number} must use KEY=VALUE: "{stripped_line}"')
            continue
        key, value = stripped_line.split("=", 1)
        key = key.strip()
        if not _ENVIRONMENT_NAME_PATTERN.match(key):
            errors.append(f'Environment line {line_number} has an invalid variable name: "{key}"')
            continue
        pairs.append((key, value.strip()))
    return pairs, errors


def get_environment_value(environment, key):
    """Gets an environment value, matching names case-insensitively on Windows.

    Args:
        environment (dict): Environment to search.
        key (str): Variable name.

    Returns:
        str: Value, or an empty string when the variable is missing.
    """
    if key in environment:
        return str(environment[key])
    if os.name == "nt":
        lowered_key = key.lower()
        for existing_key, value in environment.items():
            if existing_key.lower() == lowered_key:
                return str(value)
    return ""


def set_environment_value(environment, key, value):
    """Sets an environment value, replacing a differently cased key on Windows.

    Args:
        environment (dict): Environment to update in place.
        key (str): Variable name.
        value (str): Variable value.
    """
    if os.name == "nt":
        lowered_key = key.lower()
        for existing_key in list(environment.keys()):
            if existing_key.lower() == lowered_key and existing_key != key:
                environment.pop(existing_key)
    environment[key] = str(value)


def expand_environment_references(value, environment):
    """Expands ``${NAME}`` and ``%NAME%`` references using an environment.

    Args:
        value (str): Value that may reference other variables.
        environment (dict): Environment used for lookups.

    Returns:
        str: Expanded value. Unknown variables expand to an empty string.
    """

    def replace_reference(match):
        """Replaces one variable reference.

        Args:
            match (re.Match): Reference match.

        Returns:
            str: Referenced value.
        """
        key = match.group(1) or match.group(2)
        return get_environment_value(environment, key)

    return _ENVIRONMENT_REFERENCE_PATTERN.sub(replace_reference, str(value or ""))


def build_process_environment(base_environment, inherit_environment, batch_values, override_pairs):
    """Builds the environment for a command process.

    Overrides are applied last and in order, so a later line can extend an
    earlier one, for example ``PATH=C:/tools;${PATH}``.

    Args:
        base_environment (dict): Parent process environment.
        inherit_environment (bool): Whether to start from the parent environment.
        batch_values (dict): Batch-provided variables such as BATCH_INPUT.
        override_pairs (list): Ordered (key, value) overrides with tokens already resolved.

    Returns:
        dict: Environment dictionary for the process.
    """
    environment = {}
    if inherit_environment:
        environment.update({str(key): str(value) for key, value in (base_environment or {}).items()})
    else:
        for required_key in ("SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATH", "TEMP", "TMP", "HOME"):
            required_value = get_environment_value(base_environment or {}, required_key)
            if required_value:
                set_environment_value(environment, required_key, required_value)
    for key, value in (batch_values or {}).items():
        set_environment_value(environment, key, value)
    for key, value in override_pairs or []:
        set_environment_value(environment, key, expand_environment_references(value, environment))
    return environment


def build_batch_environment_name(key):
    """Builds the BATCH_ENV_ variable name for a project variable.

    Args:
        key (str): Project environment variable key.

    Returns:
        str: Process environment variable name.
    """
    return "BATCH_ENV_{0}".format(re.sub(r"[^A-Za-z0-9_]", "_", str(key)).upper())


def parse_exit_codes(text):
    """Parses accepted exit codes.

    Supports single values, comma lists, and ranges, for example ``0, 3-7``.
    ``*`` or ``any`` accepts every exit code.

    Args:
        text (str): Exit-code rule text.

    Returns:
        tuple: (accepted codes as a set, or None for any code; list of errors).
    """
    raw_text = str(text if text is not None else "").strip()
    if not raw_text:
        return {0}, []
    if raw_text.lower() in ANY_EXIT_CODE_TOKENS:
        return None, []
    accepted_codes = set()
    errors = []
    for part in raw_text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        range_match = re.match(r"^(-?\d+)\s*-\s*(-?\d+)$", part)
        if range_match:
            start_code = int(range_match.group(1))
            end_code = int(range_match.group(2))
            if start_code > end_code:
                errors.append(f'Exit code range "{part}" must go from low to high.')
                continue
            accepted_codes.update(range(start_code, end_code + 1))
            continue
        if re.match(r"^-?\d+$", part):
            accepted_codes.add(int(part))
            continue
        errors.append(f'Invalid exit code "{part}". Use numbers, ranges like 0-7, or "*".')
    if not accepted_codes and not errors:
        accepted_codes.add(0)
    return accepted_codes, errors


def is_exit_code_accepted(exit_code, accepted_codes):
    """Checks whether an exit code counts as success.

    Args:
        exit_code (int): Process exit code.
        accepted_codes (set or None): Accepted codes, or None for any code.

    Returns:
        bool: True when the code is accepted.
    """
    if accepted_codes is None:
        return True
    return exit_code in accepted_codes


def is_secret_key(key):
    """Checks whether an environment variable name looks like a secret.

    Args:
        key (str): Variable name.

    Returns:
        bool: True when the value should be masked in logs.
    """
    return bool(_SECRET_KEY_PATTERN.search(str(key or "")))


def format_environment_preview(override_pairs):
    """Formats environment overrides for logs, masking secret-looking values.

    Args:
        override_pairs (list): Ordered (key, value) pairs.

    Returns:
        list: Display lines such as ``KEY=value``.
    """
    lines = []
    for key, value in override_pairs or []:
        display_value = MASKED_VALUE if is_secret_key(key) and value else value
        lines.append(f"{key}={display_value}")
    return lines


def quote_argument_for_display(argument):
    """Quotes one argument for a readable command preview.

    Args:
        argument (str): Argument text.

    Returns:
        str: Argument, wrapped in double quotes when it has spaces or is empty.
    """
    argument = str(argument)
    if not argument or any(character.isspace() for character in argument):
        return '"{0}"'.format(argument.replace('"', '\\"'))
    return argument


def format_command_for_display(command):
    """Formats a process command for logs and previews.

    Args:
        command (list or str): Argument list or shell command string.

    Returns:
        str: Readable single-line command.
    """
    if isinstance(command, (list, tuple)):
        return " ".join(quote_argument_for_display(argument) for argument in command)
    return str(command or "")


def encode_powershell_command(script_text):
    """Encodes PowerShell script text for ``-EncodedCommand``.

    Encoding avoids every quoting problem between Python, Windows, and PowerShell.

    Args:
        script_text (str): PowerShell script text.

    Returns:
        str: Base64 UTF-16LE command text.
    """
    return base64.b64encode(str(script_text or "").encode("utf-16-le")).decode("ascii")


def build_powershell_script(user_script):
    """Wraps user PowerShell text so every stream is logged as plain text.

    With redirected output, PowerShell writes errors, warnings, and progress as
    CLIXML. The wrapper merges all streams into plain text, stops on the first
    error, prints that error, and returns the last native exit code.

    Args:
        user_script (str): PowerShell script text written by the user.

    Returns:
        str: Script text ready for ``-EncodedCommand``.
    """
    return "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            "$ProgressPreference = 'SilentlyContinue'",
            "$global:LASTEXITCODE = 0",
            "try {",
            "& {",
            str(user_script or ""),
            "} 3>&1 4>&1 5>&1 6>&1 | Out-String -Stream -Width 512",
            "} catch {",
            "[Console]::Out.WriteLine(($_ | Out-String).Trim())",
            "exit 1",
            "}",
            "exit $global:LASTEXITCODE",
        ]
    )


def build_shell_command(command_text, shell_type, powershell_executable="powershell"):
    """Builds the process command for the Shell mode.

    Args:
        command_text (str): Shell command text. Multiple lines run in order.
        shell_type (str): ShellType value.
        powershell_executable (str, optional): PowerShell executable name or path.

    Returns:
        tuple: (command as list or str, use_shell flag for subprocess).
    """
    text = str(command_text or "").replace("\r\n", "\n").strip()
    if shell_type == ShellType.POWERSHELL:
        script_text = build_powershell_script(text)
        command = [
            powershell_executable,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encode_powershell_command(script_text),
        ]
        return command, False
    lines = [line.strip() for line in text.split("\n") if line.strip() and not line.strip().startswith("#")]
    if os.name == "nt":
        return " && ".join(lines), True
    return "\n".join(lines), True


def parse_host_port(text, default_host="127.0.0.1"):
    """Parses ``host:port`` or ``port`` text.

    Args:
        text (str): Port target text.
        default_host (str, optional): Host used when only a port is given.

    Returns:
        tuple: (host, port as int), or (None, None) when the text is invalid.
    """
    raw_text = str(text or "").strip()
    if not raw_text:
        return None, None
    if re.match(r"^\d+$", raw_text):
        return default_host, int(raw_text)
    host, separator, port_text = raw_text.rpartition(":")
    if not separator or not port_text.isdigit():
        return None, None
    host = host.strip("[]") or default_host
    return host, int(port_text)


def validate_ready_target(ready_check, ready_target):
    """Validates the readiness target for the selected check.

    Args:
        ready_check (str): ReadyCheck value.
        ready_target (str): Resolved target text.

    Returns:
        list: Error messages.
    """
    target = str(ready_target or "").strip()
    if not target:
        return [f'"{ready_check}" needs a target value.']
    if ready_check == ReadyCheck.URL and not re.match(r"^https?://", target, re.IGNORECASE):
        return [f'Ready URL must start with http:// or https://: "{target}"']
    if ready_check == ReadyCheck.PORT:
        host, port = parse_host_port(target)
        if host is None or not 0 < port < 65536:
            return [f'Ready port must be "port" or "host:port": "{target}"']
    return []


def mask_secrets(text, override_pairs):
    """Replaces secret override values found in text.

    Args:
        text (str): Text to clean.
        override_pairs (list): Ordered (key, value) pairs.

    Returns:
        str: Text with secret values masked.
    """
    cleaned_text = str(text)
    for key, value in override_pairs or []:
        if is_secret_key(key) and value and len(value) >= 4:
            cleaned_text = cleaned_text.replace(value, MASKED_VALUE)
    return cleaned_text
