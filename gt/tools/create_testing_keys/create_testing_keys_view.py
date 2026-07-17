"""Qt view for Create Testing Keys."""

from gt.tools.create_testing_keys import create_testing_keys_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class CreateTestingKeysView(metaclass=MayaWindowMeta):
    """Resizable Qt view for Create Testing Keys."""

    def __init__(self, parent=None, version=None):
        """Initializes the tool view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        self.controller = None
        self.offset_fields = {}
        title = model.SCRIPT_NAME
        if version:
            title += f" - (v{version})"
        self.setWindowTitle(title)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_testing_keys))
        self.setMinimumWidth(300)
        self.build_widgets()
        self.resize_to_contents()
        qt_utils.center_window(self)

    def build_widgets(self):
        """Builds all widgets and layouts."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        header = ui_qt.QtWidgets.QFrame()
        header.setStyleSheet("QFrame { background-color: #666666; }")
        header_layout = ui_qt.QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 5, 5)
        title_label = ui_qt.QtWidgets.QLabel(model.SCRIPT_NAME)
        title_label.setStyleSheet("font-weight: bold; background-color: transparent;")
        self.help_btn = ui_qt.QtWidgets.QPushButton("Help")
        self.help_btn.setStyleSheet("background-color: #666666;")
        self.help_btn.setMaximumWidth(65)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.help_btn)
        main_layout.addWidget(header)

        section_label = ui_qt.QtWidgets.QLabel("Offset Amount")
        section_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        main_layout.addWidget(section_label)

        grid_layout = ui_qt.QtWidgets.QGridLayout()
        grid_layout.setHorizontalSpacing(5)
        grid_layout.setVerticalSpacing(4)
        axis_colors = {"X": "#7f1d1d", "Y": "#1f7a35", "Z": "#1e3a78"}
        for column, axis in enumerate("XYZ", 1):
            label = ui_qt.QtWidgets.QLabel(axis)
            label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"background-color: {axis_colors[axis]}; font-weight: bold;")
            grid_layout.addWidget(label, 0, column)

        for row, (channel, row_label) in enumerate((("t", "T"), ("r", "R"), ("s", "S")), 1):
            label = ui_qt.QtWidgets.QLabel(row_label)
            label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(label, row, 0)
            for column, axis in enumerate("xyz", 1):
                attribute = f"{channel}{axis}"
                field = ui_qt.QtWidgets.QDoubleSpinBox()
                field.setDecimals(3)
                field.setRange(-1000000.0, 1000000.0)
                field.setSingleStep(0.1)
                field.setValue(0.0)
                field.setToolTip(f"Offset applied to {attribute}.")
                field.setSizePolicy(
                    ui_qt.QtLib.SizePolicy.Expanding,
                    ui_qt.QtLib.SizePolicy.Fixed,
                )
                self.offset_fields[attribute] = field
                grid_layout.addWidget(field, row, column)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        grid_layout.setColumnStretch(3, 1)
        main_layout.addLayout(grid_layout)

        self.reset_btn = ui_qt.QtWidgets.QPushButton("Reset All Offset Values")
        self.reset_btn.setStyleSheet("background-color: #4d4d4d;")
        main_layout.addWidget(self.reset_btn)

        self.inverted_checkbox = ui_qt.QtWidgets.QCheckBox("Add Inverted Offset Movement")
        self.inverted_checkbox.setChecked(True)
        self.delete_previous_checkbox = ui_qt.QtWidgets.QCheckBox("Delete Previously Created Keys")
        self.delete_previous_checkbox.setChecked(True)
        self.world_space_checkbox = ui_qt.QtWidgets.QCheckBox("Use World Space (WS) Values")
        self.world_space_checkbox.setChecked(True)
        main_layout.addWidget(self.inverted_checkbox)
        main_layout.addWidget(self.delete_previous_checkbox)
        main_layout.addWidget(self.world_space_checkbox)

        interval_layout = ui_qt.QtWidgets.QHBoxLayout()
        interval_label = ui_qt.QtWidgets.QLabel("Interval Between Frames:")
        self.interval_field = ui_qt.QtWidgets.QDoubleSpinBox()
        self.interval_field.setDecimals(1)
        self.interval_field.setRange(0.1, 1000.0)
        self.interval_field.setValue(5.0)
        self.interval_field.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Fixed,
        )
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_field, 1)
        main_layout.addLayout(interval_layout)

        self.delete_all_btn = ui_qt.QtWidgets.QPushButton("Delete All Keyframes in the Scene")
        self.delete_all_btn.setStyleSheet("background-color: #4d4d4d;")
        self.create_btn = ui_qt.QtWidgets.QPushButton("Create Testing Keyframes")
        self.create_btn.setStyleSheet("background-color: #999999; color: #111111; font-weight: bold;")
        main_layout.addWidget(self.delete_all_btn)
        main_layout.addWidget(self.create_btn)

    def get_offsets(self):
        """Gets offset values from the UI.

        Returns:
            dict: Attribute names mapped to numeric offset values.
        """
        return {attribute: field.value() for attribute, field in self.offset_fields.items()}

    def set_offsets(self, offsets):
        """Updates all displayed offset values.

        Args:
            offsets (dict): Attribute names mapped to numeric values.
        """
        for attribute, field in self.offset_fields.items():
            field.setValue(float(offsets.get(attribute, 0.0)))

    def resize_to_contents(self):
        """Resizes a floating window to its smallest useful content size."""
        try:
            if hasattr(self, "isFloating") and not self.isFloating():
                return
        except (AttributeError, RuntimeError):
            pass
        self.updateGeometry()
        self.adjustSize()
        desired_size = self.sizeHint().expandedTo(self.minimumSizeHint())
        self.resize(desired_size)
