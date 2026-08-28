"""Maya-runtime integration for GT Tools Startup Scripts.

Startup configuration data is validated by the model before this module runs
anything. Maya imports stay inside the callback and execution helpers so this
module remains importable outside Maya.
"""

from gt.tools.startup_scripts import startup_scripts_model as model
import builtins
import sys
import traceback


EVENT_INTERACTIVE_MAYA = model.RUN_MODE_INTERACTIVE_MAYA
EVENT_MAYAPY = model.RUN_MODE_MAYAPY
EVENT_FILE_OPEN = model.RUN_MODE_FILE_OPEN
EVENT_MANUAL = "Manual Run"

# Maintains the previous public event name for integrations that import it.
EVENT_MAYA_STARTUP = EVENT_INTERACTIVE_MAYA

_CALLBACK_STATE_ATTRIBUTE = "_gt_tools_startup_scripts_callback_id"
_INITIALIZED_STATE_ATTRIBUTE = "_gt_tools_startup_scripts_runtime_initialized"


def write_message(message, error=False):
    """Writes a consistently labelled Startup Scripts message to Maya's output.

    Args:
        message (str): Message body to write.
        error (bool, optional): Whether the message should use standard error.
    """
    output_stream = sys.stderr if error else sys.stdout
    output_stream.write(f"[GT Tools Startup Scripts] {message}\n")


def matches_event(configuration, event_name):
    """Checks whether one configuration should run for an event.

    Args:
        configuration (dict): Startup-script configuration.
        event_name (str): Current execution event.

    Returns:
        bool: True when the run mode includes the requested event.
    """
    if not isinstance(configuration, dict):
        return False
    if event_name == EVENT_MANUAL:
        return True
    return event_name in model.get_run_mode_events(configuration.get("run_mode"))


def get_startup_event(session_module=None):
    """Gets the current Maya startup event for this Python process.

    Args:
        session_module (module, optional): Session helper module, injected for testing.

    Returns:
        str: Interactive Maya or mayapy event name, or an empty string outside Maya.
    """
    if session_module is None:
        try:
            from gt.core import session

            session_module = session
        except Exception:
            return ""
    try:
        if session_module.is_script_in_interactive_maya():
            return EVENT_INTERACTIVE_MAYA
        if session_module.is_script_in_py_maya():
            return EVENT_MAYAPY
    except Exception:
        return ""
    return ""


def build_script_namespace(event_name, extra_globals=None):
    """Builds globals exposed to configured startup scripts.

    Args:
        event_name (str): Current execution event.
        extra_globals (dict, optional): Additional values, primarily for testing.

    Returns:
        dict: Namespace used for inline and external source execution.
    """
    namespace = {
        "__name__": "__gt_tools_startup_script__",
        "event_name": event_name,
        "sys": sys,
    }
    try:
        import maya.cmds as cmds

        namespace["cmds"] = cmds
    except Exception:
        pass
    if isinstance(extra_globals, dict):
        namespace.update(extra_globals)
    return namespace


def execute_source_text(source_text, source_name, namespace):
    """Executes one Python source string using a shared script namespace.

    Args:
        source_text (str): Python source code.
        source_name (str): Name displayed in tracebacks.
        namespace (dict): Globals and locals exposed to the source.

    Returns:
        bool: True when execution completed without raising an exception.
    """
    try:
        exec(compile(str(source_text or ""), source_name, "exec"), namespace, namespace)
    except Exception as exception:
        write_message(f"Failed to run source '{source_name}': {exception}", error=True)
        traceback.print_exc()
        return False
    return True


def execute_external_file(script_path, namespace):
    """Loads and executes one external Python file.

    Args:
        script_path (str): Existing Python source path.
        namespace (dict): Globals and locals exposed to the source.

    Returns:
        bool: True when execution completed without raising an exception.
    """
    try:
        source_text = model.load_script_file(script_path)
    except (IOError, OSError) as exception:
        write_message(f"Unable to read external script '{script_path}': {exception}", error=True)
        return False
    namespace["__file__"] = script_path
    return execute_source_text(source_text, script_path, namespace)


def run_script_configuration(
    configuration,
    event_name=EVENT_MANUAL,
    ignore_run_mode=False,
    ignore_run_interval=False,
    extra_globals=None,
):
    """Runs all available sources from a script configuration.

    Sources execute in this order: inline code, configured external files, and
    Python files found in configured directories. One source failure is logged
    without preventing the remaining sources from executing.

    Args:
        configuration (dict): Startup-script configuration to execute.
        event_name (str, optional): Trigger responsible for the execution.
        ignore_run_mode (bool, optional): Whether to ignore the stored trigger.
        ignore_run_interval (bool, optional): Whether to ignore the optional run frequency.
        extra_globals (dict, optional): Additional globals, primarily for testing.

    Returns:
        bool: True when at least one source ran successfully.
    """
    if not model.is_script_configuration_valid(configuration):
        write_message("Skipped an invalid script configuration.", error=True)
        return False
    if not configuration.get("enabled", True):
        return False
    if not ignore_run_mode and not matches_event(configuration, event_name):
        return False
    if not ignore_run_interval and not model.is_script_run_due(configuration):
        return False
    if not model.has_runnable_source(configuration):
        return False

    script_name = configuration.get("name") or "Startup Script"
    should_print = configuration.get("print_execution_message", True)
    if should_print:
        write_message(f"Running '{script_name}' during {event_name}.")

    namespace = build_script_namespace(event_name, extra_globals=extra_globals)
    ran_successfully = False
    inline_source = configuration.get("script_text") or ""
    if inline_source.strip():
        inline_name = f"<gt_startup_scripts:{script_name}>"
        ran_successfully = execute_source_text(inline_source, inline_name, namespace) or ran_successfully

    for script_path in model.get_script_paths(configuration):
        ran_successfully = execute_external_file(script_path, namespace) or ran_successfully

    if should_print and ran_successfully:
        write_message(f"Finished '{script_name}' during {event_name}.")
    return ran_successfully


def run_configurations(configurations, event_name, startup_model=None):
    """Runs every configuration that is enabled for the requested event.

    Args:
        configurations (list): Ordered startup-script configurations.
        event_name (str): Trigger responsible for the execution.
        startup_model (StartupScriptsModel, optional): Model used to persist scheduled run dates.

    Returns:
        int: Number of configurations that ran at least one source successfully.
    """
    run_count = 0
    successful_script_ids = []
    for configuration in configurations if isinstance(configurations, list) else []:
        if run_script_configuration(configuration, event_name=event_name):
            run_count += 1
            successful_script_ids.append(configuration.get("id"))
    if startup_model and successful_script_ids:
        startup_model.record_scheduled_runs(successful_script_ids)
    return run_count


def get_callback_id():
    """Gets the current Maya file-open callback identifier.

    Returns:
        object: Callback identifier, or None when no callback is installed.
    """
    return getattr(builtins, _CALLBACK_STATE_ATTRIBUTE, None)


def set_callback_id(callback_id):
    """Stores the callback identifier outside this module's reloadable globals.

    Args:
        callback_id (object): Maya callback identifier, or None.
    """
    setattr(builtins, _CALLBACK_STATE_ATTRIBUTE, callback_id)


def remove_file_open_callback():
    """Removes the existing Maya file-open callback when one is installed.

    Returns:
        bool: True when a callback was removed.
    """
    callback_id = get_callback_id()
    if callback_id is None:
        return False
    try:
        import maya.api.OpenMaya as om

        om.MMessage.removeCallback(callback_id)
    except Exception:
        pass
    set_callback_id(None)
    return True


def _on_file_opened(*args):
    """Runs valid File Open configurations after Maya finishes opening a scene.

    Args:
        *args: Callback arguments provided by Maya and ignored by this handler.
    """
    startup_model = model.StartupScriptsModel()
    if not startup_model.has_valid_preferences_file():
        return
    run_configurations(startup_model.get_scripts(), EVENT_FILE_OPEN, startup_model=startup_model)


def refresh_file_open_callback():
    """Installs the file-open callback only for a valid configured preference file.

    Returns:
        bool: True when the file-open callback is currently installed.
    """
    remove_file_open_callback()
    startup_model = model.StartupScriptsModel()
    if not startup_model.has_valid_preferences_file():
        return False
    configurations = startup_model.get_scripts()
    has_file_open_scripts = any(
        configuration.get("enabled", True)
        and matches_event(configuration, EVENT_FILE_OPEN)
        and model.has_runnable_source(configuration)
        for configuration in configurations
    )
    if not has_file_open_scripts:
        return False
    try:
        import maya.api.OpenMaya as om

        callback_id = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, _on_file_opened)
        set_callback_id(callback_id)
        return True
    except Exception as exception:
        write_message(f"Unable to install the file-open callback: {exception}", error=True)
        return False


def initialize_startup_scripts():
    """Runs valid startup scripts for the current Maya context.

    This is called after GT Tools has loaded. It runs only configurations whose
    run mode includes the current Interactive Maya or mayapy event. The File
    Open callback is installed for Interactive Maya only.

    Returns:
        bool: True when valid preferences were found and initialized.
    """
    if getattr(builtins, _INITIALIZED_STATE_ATTRIBUTE, False):
        return False
    setattr(builtins, _INITIALIZED_STATE_ATTRIBUTE, True)
    startup_event = get_startup_event()
    if not startup_event:
        return False
    startup_model = model.StartupScriptsModel()
    if not startup_model.has_valid_preferences_file():
        return False
    configurations = startup_model.get_scripts()
    if startup_event == EVENT_INTERACTIVE_MAYA:
        refresh_file_open_callback()
    run_configurations(configurations, startup_event, startup_model=startup_model)
    return True
