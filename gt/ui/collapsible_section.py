"""
Collapsible Section - A titled section whose content can be shown or hidden with its header.

Import Line:
    from gt.ui.collapsible_section import CollapsibleSection

Example:
    section = CollapsibleSection("Placement", expanded=False)
    section.content_layout.addWidget(QtWidgets.QLabel("Content"))
    section.toggled.connect(lambda expanded: print(expanded))
"""

import gt.ui.qt_import as ui_qt


class CollapsibleSection(ui_qt.QtWidgets.QWidget):
    """Section with a clickable header that expands or collapses its content."""

    toggled = ui_qt.QtCore.Signal(bool)

    def __init__(self, title, parent=None, expanded=True):
        """Initializes the section.

        Args:
            title (str): Header text.
            parent (QWidget, optional): Parent widget.
            expanded (bool, optional): Initial state.
        """
        super().__init__(parent)
        self.header_button = ui_qt.QtWidgets.QToolButton()
        self.header_button.setText(title)
        self.header_button.setCheckable(True)
        self.header_button.setChecked(expanded)
        self.header_button.setToolButtonStyle(ui_qt.QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header_button.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Policy.Expanding, ui_qt.QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.header_button.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; padding: 4px 2px; text-align: left; }"
            "QToolButton:hover { color: rgb(200, 200, 200); }"
        )
        self.content_widget = ui_qt.QtWidgets.QWidget()
        self.content_layout = ui_qt.QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(14, 2, 2, 6)
        self.content_layout.setSpacing(5)
        separator = ui_qt.QtWidgets.QFrame()
        separator.setFrameShape(ui_qt.QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(ui_qt.QtWidgets.QFrame.Shadow.Sunken)
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.header_button)
        main_layout.addWidget(self.content_widget)
        self.header_button.toggled.connect(self._on_header_toggled)
        self._update_state(expanded)

    def _on_header_toggled(self, expanded):
        """Updates the content when the header is clicked.

        Args:
            expanded (bool): New state.
        """
        self._update_state(expanded)
        self.toggled.emit(expanded)

    def _update_state(self, expanded):
        """Shows or hides the content and updates the arrow.

        Args:
            expanded (bool): Whether the content is visible.
        """
        arrow = ui_qt.QtCore.Qt.ArrowType.DownArrow if expanded else ui_qt.QtCore.Qt.ArrowType.RightArrow
        self.header_button.setArrowType(arrow)
        self.content_widget.setVisible(expanded)

    def set_expanded(self, expanded):
        """Expands or collapses the section without emitting toggled.

        Args:
            expanded (bool): New state.
        """
        blocked = self.header_button.blockSignals(True)
        self.header_button.setChecked(expanded)
        self.header_button.blockSignals(blocked)
        self._update_state(expanded)

    def is_expanded(self):
        """Checks whether the section is expanded.

        Returns:
            bool: Expanded state.
        """
        return self.header_button.isChecked()
