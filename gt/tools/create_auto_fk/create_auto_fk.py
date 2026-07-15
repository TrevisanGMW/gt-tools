"""Compatibility functions for the former Create Auto FK module."""

from gt.tools.create_fk_driver.create_fk_driver_model import CreateFkDriverModel

script_name = "Create FK Driver"
script_version = "?.?.?"


def build_gui_auto_fk():
    """Launches the renamed Create FK Driver interface."""
    from gt.tools.create_fk_driver import launch_tool

    return launch_tool()


def parse_text_field(textfield_data):
    """Parses legacy comma-separated field text.

    Args:
        textfield_data (str): Field text.

    Returns:
        list: Clean parsed values.
    """
    return CreateFkDriverModel.parse_comma_separated(textfield_data)


def get_short_name(obj):
    """Gets a node short name.

    Args:
        obj (str): Node path.

    Returns:
        str: Short node name.
    """
    return CreateFkDriverModel._short_name(obj)


if __name__ == "__main__":
    build_gui_auto_fk()
