"""
Color Manager Controller
"""

import gt.ui.file_dialog as ui_file_dialog
import gt.ui.qt_import as ui_qt


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


class ColorManagerController:
    """Connects the Color Manager model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (ColorManagerModel): Tool model.
            view (ColorManagerView): Tool view.
        """
        self.model = model
        self.view = view
        self.view.controller = self

    def start(self):
        """Loads preferences and opens the tool."""
        self.model.load_preferences()
        self.view.update_from_model(self.model)
        self.view.show()

    def set_current_color(self, color):
        """Updates the current color.

        Args:
            color (list): RGB color.
        """
        self.model.set_current_color(color)

    def set_color_mode(self, value):
        """Updates the viewport color mode.

        Args:
            value (str): Color mode.
        """
        self.model.color_mode = value
        self.model.save_preferences()

    def set_target(self, value):
        """Updates the target mode.

        Args:
            value (str): Target mode.
        """
        self.model.target = value
        self.model.save_preferences()

    def set_outliner(self, value):
        """Updates whether outliner colors should be affected.

        Args:
            value (bool): Checkbox state.
        """
        self.model.set_outliner = bool(value)
        self.model.save_preferences()

    def set_viewport(self, value):
        """Updates whether viewport colors should be affected.

        Args:
            value (bool): Checkbox state.
        """
        self.model.set_viewport = bool(value)
        self.model.save_preferences()

    def set_auto_adjust_outliner_to_viewport(self, value):
        """Updates outliner-to-viewport correction.

        Args:
            value (bool): Checkbox state.
        """
        self.model.auto_adjust_outliner_to_viewport = bool(value)
        self.model.save_preferences()

    def set_auto_adjust_viewport_to_outliner(self, value):
        """Updates viewport-to-outliner correction.

        Args:
            value (bool): Checkbox state.
        """
        self.model.auto_adjust_viewport_to_outliner = bool(value)
        self.model.save_preferences()

    def cycle_ui_mode(self):
        """Cycles Minimal, Default, and Complete UI modes."""
        self.model.cycle_ui_mode()
        self.view.set_ui_mode(self.model.ui_mode)

    def apply_preset_color(self, color):
        """Applies a preset color immediately.

        Args:
            color (list): RGB color.
        """
        from gt.tools.color_manager import color_manager_model as model_module

        converted_color = model_module.convert_color_from_outliner(
            color,
            self.model.auto_adjust_outliner_to_viewport,
        )
        self.model.set_current_color(converted_color)
        self.view.set_current_color(converted_color)
        self.apply_color(reset=False)

    def apply_saved_color(self, color):
        """Applies a saved color immediately.

        Args:
            color (list): RGB color.
        """
        self.model.set_current_color(color)
        self.view.set_current_color(color)
        self.apply_color(reset=False)

    def get_selection_color(self):
        """Reads a color from the current Maya selection."""
        color = self.model.get_selection_color()
        if color:
            self.model.set_current_color(color)
            self.view.set_current_color(color)

    def apply_color(self, reset=False):
        """Applies or resets color on the current Maya selection.

        Args:
            reset (bool, optional): Whether to reset instead of apply.
        """
        self.model.set_current_color(self.view.get_current_color())
        self.model.apply_color(reset=reset)

    def save_current_color(self):
        """Saves the current color and refreshes saved swatches."""
        self.model.set_current_color(self.view.get_current_color())
        self.model.save_current_color()
        self.view.refresh_saved_colors(self.model.saved_colors)

    def delete_current_color(self):
        """Deletes the current saved color or the last saved color."""
        self.model.set_current_color(self.view.get_current_color())
        self.model.delete_current_color()
        self.view.refresh_saved_colors(self.model.saved_colors)

    def delete_saved_color(self, index, *args):
        """Deletes a saved color by index.

        Args:
            index (int): Saved color index.
            *args: Optional Qt signal arguments.
        """
        self.model.delete_saved_color(index)
        self.view.refresh_saved_colors(self.model.saved_colors)

    def clear_saved_colors(self):
        """Clears all saved colors after confirmation."""
        result = ui_qt.QtWidgets.QMessageBox.question(
            self.view,
            "Clear Saved Colors",
            "Clear all saved colors?",
            ui_qt.QtWidgets.QMessageBox.Yes | ui_qt.QtWidgets.QMessageBox.No,
            ui_qt.QtWidgets.QMessageBox.No,
        )
        if result == ui_qt.QtWidgets.QMessageBox.Yes:
            self.model.clear_saved_colors()
            self.view.refresh_saved_colors(self.model.saved_colors)

    def import_saved_colors(self):
        """Imports saved colors from a JSON file."""
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            write_mode=False,
            caption="Import Saved Colors",
            file_filter="JSON Files (*.json);;All Files (*.*)",
        )
        if not file_path:
            return
        added_count = self.model.import_saved_colors(file_path)
        self.view.refresh_saved_colors(self.model.saved_colors)
        self.show_in_view_message("Imported {0} Color Manager saved color(s).".format(added_count))

    def export_saved_colors(self):
        """Exports saved colors to a JSON file."""
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            write_mode=True,
            caption="Export Saved Colors",
            file_filter="JSON Files (*.json);;All Files (*.*)",
        )
        if not file_path:
            return
        written_path = self.model.export_saved_colors(file_path)
        if written_path:
            print('Exported Color Manager saved colors to: "{0}"'.format(written_path))
            self.show_in_view_message("Exported Color Manager saved colors.")

    @staticmethod
    def show_in_view_message(message):
        """Shows a Maya in-view message when available.

        Args:
            message (str): Message text.
        """
        try:
            cmds = get_maya_cmds()
            cmds.inViewMessage(amg=str(message), pos="botLeft", fade=True, alpha=0.9)
        except Exception:
            print(message)
