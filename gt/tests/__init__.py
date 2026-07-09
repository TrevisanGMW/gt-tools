"""
Tests module
"""

import unittest
import logging
import inspect
import ast
import sys
import os
import re

# Import Tests
import gt.tests.test_curve_library as test_curve_library
import gt.tests.test_auto_rigger as test_auto_rigger
import gt.tests.test_sample_tool as test_sample_tool
import gt.tests.test_utils as test_utils
import gt.tests.test_core as test_core
import gt.tests.test_ui as test_ui

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)

# Paths to Append
source_dir = os.path.dirname(__file__)
package_root_dir = os.path.dirname(source_dir)
package_parent_dir = os.path.dirname(package_root_dir)
for to_append in [source_dir, package_root_dir, package_parent_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)

# Modules to Test
modules_to_test = [
    # Ui
    test_ui.test_input_window_text,
    test_ui.test_line_text_widget,
    test_ui.test_maya_menu,
    test_ui.test_progress_bar,
    test_ui.test_python_output_view,
    test_ui.test_qt_utils,
    test_ui.test_resource_library,
    # Tools
    test_auto_rigger.test_rig_utils,
    test_auto_rigger.test_rig_framework,
    test_auto_rigger.test_rig_constants,
    test_auto_rigger.test_module_arm,
    test_auto_rigger.test_module_biped_arm,
    test_auto_rigger.test_module_biped_leg,
    test_auto_rigger.test_module_biped_finger,
    test_auto_rigger.test_module_root,
    test_auto_rigger.test_module_spine,
    test_auto_rigger.test_module_head,
    test_auto_rigger.test_module_utils,
    test_auto_rigger.test_module_chain,
    test_auto_rigger.test_module_ribbon,
    test_auto_rigger.test_template_biped,
    test_curve_library.test_curve_library_model,
    test_sample_tool.test_sample_tool_model,
    # Core
    test_core.test_anim,
    test_core.test_attr,
    test_core.test_blendshape,
    test_core.test_color,
    test_core.test_camera,
    test_core.test_cleanup,
    test_core.test_constraint,
    test_core.test_control_data,
    test_core.test_control,
    test_core.test_curve,
    test_core.test_io,
    test_core.test_display,
    test_core.test_feedback,
    test_core.test_hierarchy,
    test_core.test_iterable,
    test_core.test_joint,
    test_core.test_logger,
    test_core.test_material,
    test_core.test_math,
    test_core.test_mesh,
    test_core.test_namespace,
    test_core.test_naming,
    test_core.test_node,
    test_core.test_outliner,
    test_core.test_playblast,
    test_core.test_plugin,
    test_core.test_prefs,
    test_core.test_rbf,
    test_core.test_rigging,
    test_core.test_scene,
    test_core.test_selection,
    test_core.test_session,
    test_core.test_skin,
    test_core.test_str,
    test_core.test_surface,
    test_core.test_transform,
    test_core.test_undo,
    test_core.test_uuid,
    test_core.test_version,
    # Utils
    test_utils.test_fbx,
    test_utils.test_request,
    test_utils.test_system,
    test_utils.test_hypertext,
]


# -------------------------------------------- Unittests ---------------------------------------------
def get_test_suites_from_modules(module_list):
    """
    Get test suits from list of modules
    Args:
        module_list (list): A list of modules
    Returns:
        a list of test suites
    """
    all_suites = []
    for module in module_list:
        all_suites.append(unittest.TestLoader().loadTestsFromModule(module))
    return all_suites


def run_test_modules(module_list):
    """
    Run provided tests and returns the results
    Args:
        module_list (list): A list of modules
    Returns:
        A list of test results
    """
    results = []
    for suite in get_test_suites_from_modules(module_list):
        results.append(unittest.TextTestRunner(verbosity=1).run(suite))
    return results


def strip_ansi(text):
    """
    Removes ANSI escape sequences (e.g., color codes) from a string.

    Args:
        text (str): The input string which may contain ANSI color codes.

    Returns:
        str: The string with all ANSI escape sequences removed.
    """
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", text)


def pad_ansi(text, width):
    """
    Pads a string that may contain ANSI codes so its visible (color-free) length matches the desired width.

    Args:
        text (str): The input string, possibly with ANSI formatting.
        width (int): The target visible width for the string.

    Returns:
        str: The input string with added padding spaces to ensure proper alignment in formatted output.
    """
    visible_length = len(strip_ansi(text))
    return text + " " * (width - visible_length)


def dict_to_markdown_table(dictionary):
    """
    Converts a dictionary to a Markdown table with perfectly aligned columns,
    even when cells contain ANSI-colored strings.
    """
    for key, value in dictionary.items():
        if not isinstance(value, list):
            dictionary[key] = [value]

    headers = list(dictionary.keys())
    num_rows = max(len(dictionary[key]) for key in dictionary)
    rows = [[] for _ in range(num_rows)]

    for key in headers:
        values = dictionary[key]
        for i in range(num_rows):
            if i < len(values):
                rows[i].append(str(values[i]))
            else:
                rows[i].append("")

    # Determine the maximum visible width of each column (ignoring ANSI codes)
    col_widths = [max(len(strip_ansi(str(row[i]))) for row in rows + [headers]) for i in range(len(headers))]

    # Build table string
    md_table = "| " + " | ".join([pad_ansi(header, col_widths[i]) for i, header in enumerate(headers)]) + " |\n"
    md_table += "|-" + "-|-".join(["-" * col_widths[i] for i in range(len(headers))]) + "-|\n"
    for row in rows:
        md_table += "| " + " | ".join([pad_ansi(row[i], col_widths[i]) for i in range(len(headers))]) + " |\n"

    return md_table


def regex_module_name(module):
    """
    Args:
        module (module): A module to extract the name
    Returns:
        String without extra module and from portions. In case operation fails, module is returned as a string
        e.g.
        "<module 'test_module.test_module' from 'path'>"   becomes    "test_module.test_module"
    """
    find_file_regex = "(?<=module ').+(?=' from)"  # Ignore "<module " and " from 'path'>"
    result = re.findall(find_file_regex, str(module))
    if result:
        return result[0]
    else:
        return str(module)


def regex_file_from_failure_or_error(message):
    """
    Formats the failure or error message string into simpler string that contains the filename and line number
    Args:
        message (string): The failure/error message string which includes traceback for finding where the tests failed.
    Returns:
        String with the file, line number and test name.
        In case operation fails, the entire failure/error message is returned instead.
    """
    find_file_regex = "(?=File).+(?<=, line).+"  # Keep only file line
    result = re.findall(find_file_regex, message)
    if result:
        return result[0]
    else:
        return str(message)


def run_unittests_with_summary(print_results=True, print_traceback=False):
    """
    Runs all the unit tests found in the "modules_to_test" and generates a report
    Args:
        print_results (bool, optional): If active it prints the results
        print_traceback (bool, optional): If active, it will print traceback details of any errors/failures.
    Returns:
        str: Results in a Markdown table format
    """
    ran_counter = 0
    failed_counter = 0
    errors_counter = 0
    module_failures = {}
    module_errors = {}
    errors = []
    failures = []
    for name, result in zip(modules_to_test, run_test_modules(modules_to_test)):
        ran_counter += result.testsRun
        failed_counter += len(result.failures)
        errors_counter += len(result.errors)
        errors += result.errors
        failures += result.failures
        if len(result.failures) > 0:
            module = regex_module_name(name)
            first_failure = result.failures[0][1]
            module_failures[module] = regex_file_from_failure_or_error(first_failure)
        if len(result.errors) > 0:
            module = regex_module_name(name)
            first_error = result.errors[0][1]
            module_errors[module] = regex_file_from_failure_or_error(first_error)

    tests_summary = {"Test Runner Summary": ["Ran", "Failed"], "": [ran_counter, failed_counter]}
    if errors_counter:
        tests_summary.get("Test Runner Summary").append("Errors")
        tests_summary.get("").append(str(errors_counter))

    output_string = "\n"
    output_string += dict_to_markdown_table(tests_summary)

    # Add color
    if len(module_failures) > 0 or len(module_errors) > 0:
        output_string = f"\033[91m{output_string}\033[0m"
    else:
        output_string = f"\033[92m{output_string}\033[0m"

    # Add failures
    color_code = "\033[93m"  # Yellow
    reset_code = "\033[0m"
    if len(module_failures) > 0:
        modules = list(module_failures.keys())
        files = list(module_failures.values())
        module_failures = {"Failures": modules, "Source": files}
        # output_string += "\n" + dict_to_markdown_table(module_failures)
        _output_string = f"\n{color_code}{dict_to_markdown_table(module_failures)}"  # \033[0m"
        pattern = re.compile(r"\033\[0m(?!$)")
        _output_string = f"{pattern.sub(reset_code + color_code, _output_string)}\033[0m"
        output_string += _output_string
    if len(module_errors) > 0:
        modules = list(module_errors.keys())
        files = list(module_errors.values())
        module_errors = {"Errors": modules, "Source": files}
        # output_string += "\n" + dict_to_markdown_table(module_errors)
        _output_string = f"\n{color_code}{dict_to_markdown_table(module_errors)}"  # \033[0m"
        pattern = re.compile(r"\033\[0m(?!$)")
        _output_string = f"{pattern.sub(reset_code + color_code, _output_string)}\033[0m"
        output_string += _output_string

    if print_traceback and (errors or failures):
        for index, error in enumerate(errors):
            print(f'\n{"-" * 40} Error {str(index + 1).zfill(2)}: {"-" * 40}')
            print(error[0])
            print(error[1])
        for index, fail in enumerate(failures):
            print(f'\n{"-" * 40} Failure {str(index + 1).zfill(2)}: {"-" * 40}')
            print(fail[0])
            print(fail[1])

    if print_results:
        print(output_string)

    return output_string


# -------------------------------------------- Docstrings ---------------------------------------------
def find_files_by_extension(directory, extensions, exclude_dirs=None):
    """
    Recursively yield files in 'directory' with extensions in 'extensions',
    skipping directories listed in 'exclude_dirs'.

    Args:
        directory (str): Root directory to search.
        extensions (list of str): File extensions to include (e.g., ['.py']).
        exclude_dirs (list of str or None): Directories to exclude from search.

    Yields:
        str: Paths to files matching the extensions.
    """
    exclude_dirs = set(os.path.abspath(d) for d in (exclude_dirs or []))
    root_directory = os.path.abspath(directory)

    for root, dirs, files in os.walk(root_directory):
        abs_root = os.path.abspath(root)

        if any(abs_root.startswith(excluded) for excluded in exclude_dirs):
            dirs[:] = []  # prevent descending into excluded dirs
            continue

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                yield os.path.join(root, file)


def extract_args_from_docstring(docstring):
    """
    Extract argument names from the Args section of a Google-style docstring.

    Args:
        docstring (str): The docstring text.

    Returns:
        set: Argument names documented in the docstring.
    """
    if not docstring:
        return set()

    lines = docstring.splitlines()
    arg_names = set()
    in_args_section = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if not in_args_section and stripped.lower().startswith("args:"):
            in_args_section = True
            continue

        if in_args_section:
            # Stop if new section starts, e.g., Returns:
            if re.match(r"^\s*[A-Z][a-zA-Z]+:", stripped) and not re.match(
                r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*(\([^)]+\))?\s*:", stripped
            ):
                break

            match = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(\([^)]+\))?\s*:", line)
            if match:
                arg_name = match.group(1)
                arg_names.add(arg_name)

    return arg_names


def is_in_main_block(node, main_blocks):
    """
    Check if a given AST node is inside any of the recorded main blocks.

    Args:
        node (ast.AST): The node to check.
        main_blocks (set): Set of main block AST nodes (e.g., 'if __name__ == "__main__"').

    Returns:
        bool: True if 'node' is inside any main block, False otherwise.
    """
    current = node
    while hasattr(current, "parent"):
        current = current.parent
        if current in main_blocks:
            return True
    return False


def detect_missing_docstrings(file_path, include_classes=False, include_functions=True):
    """
    Check docstrings for the given file.

    Args:
        file_path (str): Path to the Python file to check.
        include_classes (bool): Whether to check classes for docstrings.
        include_functions (bool): Whether to check functions for docstrings.

    Returns:
        tuple: (results, checked_count)
            results (dict): Keys are "file_path:lineno" strings, values are message strings
                            explaining what's missing or wrong in the docstring.
            checked_count (int): Number of classes/functions checked for docstrings.
    """
    results = {}
    checked_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            source = f.read()
            node = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            results[file_path] = f"Skipping {file_path}: syntax error - {e}"
            return results, checked_count

    # Annotate parents for each node (to help detect context)
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent

    # Find all "if __name__ == '__main__':" blocks
    main_blocks = set()
    for item in ast.walk(node):
        if isinstance(item, ast.If):
            test = item.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                main_blocks.add(item)

    for item in ast.walk(node):
        if isinstance(item, ast.ClassDef):
            if not include_classes:
                continue
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not include_functions:
                continue
        else:
            continue

        if is_in_main_block(item, main_blocks):
            continue

        # Count this item as checked
        checked_count += 1

        name = item.name
        obj_type = "Class" if isinstance(item, ast.ClassDef) else "Function"
        docstring = ast.get_docstring(item)
        lineno = item.lineno
        key = f"{file_path}:{lineno}"

        if docstring is None:
            results[key] = f"{obj_type} '{name}' is missing a docstring"
            continue

        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arg_names = [arg.arg for arg in item.args.args if arg.arg not in {"self", "cls"}]
            doc_args = extract_args_from_docstring(docstring)
            undocumented_args = set(arg_names) - doc_args
            if undocumented_args:
                results[key] = f"Function '{name}' is missing doc entries for: {', '.join(sorted(undocumented_args))}"

    return results, checked_count


def run_docstring_checks_with_summary(include_classes=False):
    """
    Run docstring tests on Python files in the parent directory of the script's folder,
    excluding the folder where the script lives (e.g., 'tests').

    Args:
        include_classes (bool): Whether to check classes for docstrings. Default is False.

    Prints:
        Messages about missing docstrings or undocumented args collected from all files.
    """
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    script_folder = os.path.dirname(os.path.abspath(caller_file))
    root_directory = os.path.abspath(os.path.join(script_folder, os.pardir))
    exclude_dirs = [script_folder]

    missing_docstrings_dict = {}

    checked_counter = 0
    for py_file in find_files_by_extension(root_directory, [".py"], exclude_dirs=exclude_dirs):
        results, checked_count = detect_missing_docstrings(py_file, include_classes=include_classes)
        missing_docstrings_dict.update(results)
        checked_counter += checked_count
    failed_counter = len(missing_docstrings_dict.items())

    tests_summary = {"Docstrings Summary ": ["Inspected", "Missing"], "": [checked_counter, failed_counter]}

    output_string = "\n"
    output_string += dict_to_markdown_table(tests_summary)

    # Add color
    if failed_counter > 0:
        output_string = f"\033[91m{output_string}\033[0m"
    else:
        output_string = f"\033[92m{output_string}\033[0m"

    # Include Issues
    if len(missing_docstrings_dict) > 0:
        functions_raw = list(missing_docstrings_dict.keys())
        functions = []
        for func in functions_raw:
            functions.append(f'\033[4;95m"{func}"\033[0m')
        messages = list(missing_docstrings_dict.values())
        missing_docstrings = {"Function": functions, "Issue": messages}
        color_code = "\033[93m"
        reset_code = "\033[0m"
        _output_string = f"\n{color_code}{dict_to_markdown_table(missing_docstrings)}"  # \033[0m"
        pattern = re.compile(r"\033\[0m(?!$)")
        _output_string = f"{pattern.sub(reset_code+color_code, _output_string)}\033[0m"
        output_string += _output_string

    # Print results
    print(output_string)


# -------------------------------------------- Dependencies -------------------------------------------
def run_import_dependencies_checks():
    """
    Checks if the required dependencies are installed.

    This function verifies the presence of each package listed in the `dependencies` list.
    If any package is missing, it prints an error message indicating which dependency
    is not installed and suggests running a batch file to install them.
    """
    dependencies = ["numpy", "scipy"]
    is_missing = False
    for package in dependencies:
        try:
            __import__(package)
        except ImportError:
            print(f"\n\033[91mError: The package '{package}' is a required dependency but is not installed.\033[0m")

            is_missing = True
    if is_missing:
        print(f'\033[93mUse the batch file "tests/install_dependencies.bat" to fix that.\033[0m')


if __name__ == "__main__":
    run_import_dependencies_checks()
    run_unittests_with_summary(print_results=True, print_traceback=True)
    run_docstring_checks_with_summary(include_classes=False)  # Does not check unittests directory.
