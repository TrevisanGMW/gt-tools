"""Shared file statistics and preview controls for Batch Processor input editors."""

from html import escape
from gt.ui import qt_import as qt
from gt.ui import resource_library as resources


class InputSourceFeedbackWidget(qt.QtWidgets.QWidget):
    """Displays input statistics and exposes refresh and resolved path actions."""

    def __init__(self, refresh_callback, preview_callback, parent=None):
        """Builds a compact statistics label and centered action buttons.

        Args:
            refresh_callback (callable): Function that refreshes the input snapshot.
            preview_callback (callable): Function that previews resolved input paths.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        layout = qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.label = qt.QtWidgets.QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        buttons_layout = qt.QtWidgets.QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        self.refresh_button = qt.QtWidgets.QPushButton("Refresh")
        self.refresh_button.setIcon(qt.QtGui.QIcon(resources.Icon.ui_reset))
        self.refresh_button.setToolTip("Refresh the input list and its statistics.")
        self.refresh_button.clicked.connect(refresh_callback)
        self.preview_button = qt.QtWidgets.QPushButton("Show Resolved")
        self.preview_button.setIcon(qt.QtGui.QIcon(resources.Icon.ui_env_var))
        self.preview_button.setToolTip("Show all resolved input paths that will be processed.")
        self.preview_button.clicked.connect(preview_callback)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.preview_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def set_statistics(self, statistics, extra_rows=None):
        """Updates file statistics and optional task-specific count rows.

        Args:
            statistics (dict): Counts and extension mappings returned by an input task.
            extra_rows (list, optional): Additional rows of (label, value) pairs.
        """
        extension_counts = statistics.get("extension_counts") or {}
        input_counts = statistics.get("resolved_extension_counts") or {}
        rows = [
            [("Input Files", statistics.get("resolved_count", 0)),
             ("Total Files", statistics.get("total_count", 0)),
             ("File Types", statistics.get("file_type_count", 0))],
            [("Found Types", self.format_extension_list(extension_counts)),
             ("Input Types", self.format_extension_list(input_counts))],
        ]
        rows.extend(extra_rows or [])
        self.label.setText("<br>".join(" &nbsp; | &nbsp; ".join(
            f'<span style="color:#888888;">{escape(str(label))}:</span> '
            f'<span style="color:#FFFFFF;">{escape(str(value))}</span>'
            for label, value in row) for row in rows))
        found_lines = "\n".join(f"{extension}: {extension_counts[extension]}"
                                for extension in sorted(extension_counts)) or "No files found."
        input_lines = "\n".join(f"{extension}: {input_counts[extension]}"
                                for extension in sorted(input_counts)) or "No input files matched."
        extra_lines = "\n".join(f"{label}: {value}" for row in extra_rows or [] for label, value in row)
        self.label.setToolTip(f"Found Types:\n{found_lines}\n\nInput Types:\n{input_lines}\n\n{extra_lines}".rstrip())

    @staticmethod
    def format_extension_list(extension_counts):
        """Formats discovered extensions as a readable list.

        Args:
            extension_counts (dict): Mapping of extensions to file counts.

        Returns:
            str: Comma-separated extension names, or None when no files were found.
        """
        return ", ".join(str(extension).lstrip(".") for extension in sorted(extension_counts or {})) or "None"
