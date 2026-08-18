"""Controller for Copy/Paste Animation."""

import logging

import gt.ui.qt_import as ui_qt
import gt.ui.python_output_view as ui_python_output_view
from gt.core import anim as core_anim
from gt.tools.anim_copy_paste import anim_copy_paste_model as copy_model


logger = logging.getLogger(__name__)


class AnimCopyPasteController:
    """Connects Copy/Paste Animation view, model, and Maya service."""

    def __init__(self, model, view, service):
        """Initializes and displays the connected tool.

        Args:
            model (AnimCopyPasteModel): Persistent tool state.
            view (AnimCopyPasteView): Dockable Qt interface.
            service (AnimCopyPasteService): Maya runtime service.
        """
        self.model = model
        self.view = view
        self.service = service
        self.details_window = None
        self.view.controller = self
        self.model.set_clip_data(self.service.load_cached_clip())
        self.view.set_settings(self.model.get_settings())
        self._refresh_cache_summary()
        self._connect_view()
        self.view.show()
        ui_qt.QtCore.QTimer.singleShot(0, self.view.resize_to_contents)

    def _connect_view(self):
        """Connects view signals to controller actions."""
        self.view.copy_button.clicked.connect(self.copy_animation)
        self.view.details_button.clicked.connect(self.show_animation_details)
        self.view.paste_insert_button.clicked.connect(
            lambda *args: self.paste_animation(core_anim.AnimationConstants.PasteMode.INSERT)
        )
        self.view.paste_replace_button.clicked.connect(
            lambda *args: self.paste_animation(core_anim.AnimationConstants.PasteMode.REPLACE)
        )
        self.view.import_button.clicked.connect(self.import_animation)
        self.view.export_button.clicked.connect(self.export_animation)
        self.view.clear_cache_button.clicked.connect(self.clear_cache)
        self.view.help_button.clicked.connect(self.view.show_help)

    def _update_model(self):
        """Synchronizes and saves current view settings."""
        self.model.set_settings(self.view.get_settings())
        self.model.save_preferences()

    def _refresh_cache_summary(self):
        """Updates the view's current copy-cache summary."""
        self.view.set_cache_summary(self.service.get_summary(self.model.clip_data))

    def copy_animation(self):
        """Copies animation from the current selection using the configured scope."""
        self._update_model()
        nodes = self.service.get_selection()
        if not nodes and self.model.copy_scope != copy_model.AnimCopyPasteConstants.CopyScope.SELECTED:
            self._warn("Nothing selected. Select one or more animated objects and try again.")
            return
        try:
            clip_data = self.service.copy(nodes, copy_scope=self.model.copy_scope)
        except Exception as exception:
            logger.exception("Unable to copy animation.")
            self._warn(f"Copy failed: {exception}")
            return
        self.model.set_clip_data(clip_data)
        self._refresh_cache_summary()
        if not self.model.has_clip_data():
            if self.model.copy_scope == copy_model.AnimCopyPasteConstants.CopyScope.SELECTED:
                self._warn("No selected timeline keyframes were found on the selected objects.")
            else:
                self._warn("No time-keyed animation was found on the selected objects.")
            return
        scope_labels = {
            copy_model.AnimCopyPasteConstants.CopyScope.ALL: "all animation",
            copy_model.AnimCopyPasteConstants.CopyScope.SELECTED: "selected keyframes",
            copy_model.AnimCopyPasteConstants.CopyScope.BEFORE_CURRENT: "keys at and before the current frame",
            copy_model.AnimCopyPasteConstants.CopyScope.AFTER_CURRENT: "keys at and after the current frame",
        }
        self.view.set_message(
            f"Copied {scope_labels.get(self.model.copy_scope, 'animation')} to the shared persistent cache.",
            "success",
        )

    def show_animation_details(self):
        """Shows the stored animation report in a line-numbered output window."""
        if not self.model.has_clip_data():
            self.model.set_clip_data(self.service.load_cached_clip())
        output_window = ui_python_output_view.PythonOutputView(parent=self.view, editable=False)
        output_window.setWindowTitle("Stored Animation Details")
        output_window.set_python_output_text(self.service.get_details(self.model.clip_data))
        output_window.show()
        self.details_window = output_window

    def paste_animation(self, mode):
        """Pastes cached animation using the requested paste behavior.

        Args:
            mode (str): Insert or replace paste behavior.
        """
        self._update_model()
        if not self.model.has_clip_data():
            self.model.set_clip_data(self.service.load_cached_clip())
        if not self.model.has_clip_data():
            self._warn("No copied animation is available. Copy or import animation first.")
            return
        if (
            self.model.mapping_mode == copy_model.AnimCopyPasteConstants.MappingMode.NAMESPACE
            and not self.model.target_namespace
        ):
            self._warn("Enter a Target Namespace before using Namespace Swap mapping.")
            return
        if mode == core_anim.AnimationConstants.PasteMode.REPLACE and not self._confirm_replace():
            return
        targets = self.service.get_selection()
        paste_time = self.service.get_current_frame() if self.model.paste_at_current_frame else self.model.paste_frame
        try:
            result = self.service.paste(
                clip_data=self.model.clip_data,
                targets=targets,
                paste_time=paste_time,
                mode=mode,
                mapping_mode=self.model.mapping_mode,
                source_attribute=self.model.source_attribute,
                destination_attribute=self.model.destination_attribute,
                source_namespace=self.model.source_namespace,
                target_namespace=self.model.target_namespace,
                apply_euler_filter=self.model.apply_euler_filter,
            )
        except Exception as exception:
            logger.exception("Unable to paste animation.")
            self._warn(f"Paste failed: {exception}")
            return
        if not result.get("keys"):
            self._warn("No compatible target channels were found for the copied animation.")
            return
        mode_label = "inserted" if mode == core_anim.AnimationConstants.PasteMode.INSERT else "replaced"
        message = (
            f"{mode_label.capitalize()} {result['keys']} key(s) on {result['channels']} channel(s) "
            f"across {result['targets']} object(s)."
        )
        if result.get("skipped"):
            message += f" Skipped {result['skipped']} unavailable channel(s)."
        self.view.set_message(message, "success" if not result.get("skipped") else "warning")

    def import_animation(self):
        """Loads a portable animation JSON file into the shared cache."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            self.view,
            "Import Animation JSON",
            "",
            "Animation JSON (*.json);;All Files (*)",
        )
        if not file_path:
            return
        try:
            self.model.set_clip_data(self.service.import_clip(file_path))
        except Exception as exception:
            logger.exception("Unable to import animation JSON.")
            self._warn(f"Import failed: {exception}")
            return
        self._refresh_cache_summary()
        if self.model.has_clip_data():
            self.view.set_message("Animation JSON imported to the shared cache.", "success")
        else:
            self._warn("The imported file did not contain compatible animation data.")

    def export_animation(self):
        """Exports cached animation as a portable JSON file."""
        if not self.model.has_clip_data():
            self._warn("No copied animation is available to export.")
            return
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self.view,
            "Export Animation JSON",
            "animation_clip.json",
            "Animation JSON (*.json);;All Files (*)",
        )
        if not file_path:
            return
        try:
            written_path = self.service.export_clip(self.model.clip_data, file_path)
        except Exception as exception:
            logger.exception("Unable to export animation JSON.")
            self._warn(f"Export failed: {exception}")
            return
        self.view.set_message(f"Animation JSON exported to: {written_path}", "success")

    def clear_cache(self):
        """Clears the persistent copied-animation cache."""
        if not self._confirm_clear_cache():
            return
        self.service.clear_cached_clip()
        self.model.set_clip_data({})
        self._refresh_cache_summary()
        self.view.set_message("Copy/Paste Animation cache cleared.", "info")

    def _confirm_replace(self):
        """Requests confirmation before destructive replace pastes.

        Returns:
            bool: True when the user confirms replacement.
        """
        message_box = ui_qt.QtWidgets.QMessageBox
        button_type = getattr(message_box, "StandardButton", message_box)
        yes_button = getattr(button_type, "Yes")
        no_button = getattr(button_type, "No")
        response = message_box.question(
            self.view,
            "Replace Animation?",
            "Paste Replace Animation removes existing keys on every affected destination channel before pasting. "
            "This is undoable in Maya. Continue?",
            yes_button | no_button,
            no_button,
        )
        return response == yes_button

    def _confirm_clear_cache(self):
        """Requests confirmation before clearing the persistent cache.

        Returns:
            bool: True when the user confirms cache deletion.
        """
        message_box = ui_qt.QtWidgets.QMessageBox
        button_type = getattr(message_box, "StandardButton", message_box)
        yes_button = getattr(button_type, "Yes")
        no_button = getattr(button_type, "No")
        response = message_box.question(
            self.view,
            "Clear Animation Cache?",
            "This removes only Copy/Paste Animation's persistent cached JSON file. Continue?",
            yes_button | no_button,
            no_button,
        )
        return response == yes_button

    def _warn(self, message):
        """Displays a warning in the tool and Maya.

        Args:
            message (str): User-facing warning.
        """
        self.view.set_message(message, "warning")
        self.service.warn(message)
