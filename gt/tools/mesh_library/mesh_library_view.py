"""
Mesh Library View - The main GUI window class for the Curve Library tool.
"""

import gt.ui.resource_library as ui_res_lib
from gt.ui.squared_widget import SquaredWidget
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt


class MeshLibraryView(metaclass=ui_qt_utils.MayaWindowMeta):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the CurveLibraryWindow.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (MeshLibraryController): MeshLibraryController, not to be used, here so it's not deleted by
                                                 the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        # super(MeshLibraryWindow, self).__init__(parent=parent)
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        self.splitter = None
        self.search_bar = None
        self.item_list = None
        self.add_custom_button = None
        self.delete_custom_button = None
        self.build_button = None
        self.preview_image = None
        self.description = None
        self.snapshot_button = None
        self.parameters_button = None

        window_title = "Mesh Library"
        if version:
            window_title += f" - (v{str(version)})"
        self.setWindowTitle(window_title)

        self.setGeometry(100, 100, 400, 300)

        self.create_widgets()
        self.create_layout()
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_mesh_library))

        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)
        ui_qt_utils.resize_to_screen(self, percentage=30)
        ui_qt_utils.center_window(self)
        self.resize_splitter_to_screen()

    def update_preview_image(self, new_image_path=None):
        """
        Update the preview image displayed in the window.

        Args:
            new_image_path (str, optional): The path to the new image file.
                                            Defaults to None, which becomes "missing_preview_file"
        """
        if new_image_path:
            self.preview_image.set_pixmap(ui_qt.QtGui.QPixmap(new_image_path))
        else:
            self.preview_image.set_pixmap(ui_qt.QtGui.QPixmap(ui_res_lib.Icon.library_missing_file))

    def create_widgets(self):
        """Create the widgets for the window."""
        font = ui_qt.QtGui.QFont()
        font.setPointSize(10)
        self.item_list = ui_qt.QtWidgets.QListWidget()
        self.item_list.setFont(font)
        self.build_button = ui_qt.QtWidgets.QPushButton("Build")
        self.build_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        self.build_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        self.search_bar = ui_qt.QtWidgets.QLineEdit(self)
        self.search_bar.setFont(font)
        self.search_bar.setPlaceholderText("Search...")
        self.preview_image = SquaredWidget(self, center_y=False)
        # Buttons
        self.add_custom_button = ui_qt.QtWidgets.QPushButton("Save Mesh")
        add_custom_tooltip = "Saves a Maya selected Polygon/Surface element as a user-defined item in the Mesh Library"
        self.add_custom_button.setToolTip(add_custom_tooltip)
        self.add_custom_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_add))
        self.delete_custom_button = ui_qt.QtWidgets.QPushButton("Delete Mesh")
        self.delete_custom_button.setEnabled(False)
        self.delete_custom_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_remove))
        self.description = ui_qt.QtWidgets.QLabel("<description>")
        self.description.setFont(font)

        self.description.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.snapshot_button = ui_qt.QtWidgets.QPushButton("Create Snapshot")
        self.snapshot_button.setEnabled(False)
        self.snapshot_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_snapshot))
        self.parameters_button = ui_qt.QtWidgets.QPushButton("Edit Parameters")
        self.parameters_button.setEnabled(False)
        self.parameters_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_edit))
        # Initial Image Update
        self.update_preview_image()

    def create_layout(self):
        """Create the layout for the window."""

        user_mesh_action_layout = ui_qt.QtWidgets.QHBoxLayout()
        user_mesh_action_layout.addWidget(self.add_custom_button)
        user_mesh_action_layout.addWidget(self.delete_custom_button)

        custom_action_layout = ui_qt.QtWidgets.QHBoxLayout()
        custom_action_layout.addWidget(self.snapshot_button)
        custom_action_layout.addWidget(self.parameters_button)

        list_container = ui_qt.QtWidgets.QWidget()
        list_layout = ui_qt.QtWidgets.QVBoxLayout()
        list_layout.addWidget(self.search_bar)
        list_layout.addWidget(self.item_list)
        list_layout.addLayout(user_mesh_action_layout)
        list_container.setLayout(list_layout)
        list_container.setMinimumWidth(200)
        list_container.setMinimumHeight(200)

        preview_container = ui_qt.QtWidgets.QWidget()
        side_menu_layout = ui_qt.QtWidgets.QVBoxLayout()
        side_menu_layout.addWidget(self.description)
        side_menu_layout.addWidget(self.preview_image)
        side_menu_layout.addLayout(custom_action_layout)
        side_menu_layout.addWidget(self.build_button)
        preview_container.setLayout(side_menu_layout)
        preview_container.setMinimumWidth(200)
        preview_container.setMinimumHeight(200)

        self.splitter = ui_qt.QtWidgets.QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(list_container)
        self.splitter.addWidget(preview_container)

        main_layout = ui_qt.QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 11)  # Make Margins Uniform LTRB
        main_layout.addWidget(self.splitter)

    def resize_splitter_to_screen(self, percentage=20):
        """
        Resizes the splitter to match a percentage of the screen size.

        Args:
            percentage (int, optional): The percentage of the screen size that the window should inherit.
                                        Must be a value between 0 and 100. Default is 20.

        Raises:
            ValueError: If the percentage is not within the range [0, 100].
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage should be between 0 and 100")
        if ui_qt.IS_PYSIDE6:
            screen = ui_qt.QtGui.QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
        else:
            screen_geometry = ui_qt.QtWidgets.QDesktopWidget().availableGeometry(self)
        width = screen_geometry.width() * percentage / 100
        self.splitter.setSizes([width * 0.2, width * 0.60])

    def clear_view_library(self):
        """
        Clears (removes) all items from the QListWidgetItem.
        """
        self.item_list.clear()

    def add_item_view_library(self, item_name, hex_color=None, icon=None, metadata=None):
        """
        Updates the view with the provided items.

        Args:
            item_name (str): A name for the item that will be added to the list
            hex_color (str, optional): A string with a hex color to be used for the added item (e.g. "#FF0000" = Red)
            icon (QIcon, optional): A icon to be added in front of the mesh name
            metadata (dict, optional): If provided, this will be added as metadata to the item.
        """
        _item = ui_qt.QtWidgets.QListWidgetItem(item_name)
        if hex_color and isinstance(hex_color, str):
            _item.setForeground(ui_qt.QtGui.QColor(hex_color))
        if icon and isinstance(icon, ui_qt.QtGui.QIcon):
            _item.setIcon(icon)
        if metadata and isinstance(metadata, dict):
            _item.setData(ui_qt.QtLib.ItemDataRole.UserRole, metadata)
        self.item_list.addItem(_item)

    def set_delete_button_enabled(self, is_enabled):
        """
        Set the enabled state of the delete button.

        Args:
            is_enabled (bool): True to enable the delete button, False to disable it.
        """
        if isinstance(is_enabled, bool):
            self.delete_custom_button.setEnabled(is_enabled)

    def set_parameters_button_enabled(self, is_enabled):
        """
        Set the enabled state of the parameters button.

        Args:
            is_enabled (bool): True to enable the parameters button, False to disable it.
        """
        if isinstance(is_enabled, bool):
            self.parameters_button.setEnabled(is_enabled)

    def set_snapshot_button_enabled(self, is_enabled):
        """
        Set the enabled state of the snapshot button.

        Args:
            is_enabled (bool): True to enable the snapshot button, False to disable it.
        """
        if isinstance(is_enabled, bool):
            self.snapshot_button.setEnabled(is_enabled)

    def update_item_description(self, new_title, new_description):
        """
        Updates the item description label (text) with the given new description.
        Args:
            new_title (str): Title for the item description.
            new_description (str): The item description to display. (output text)
        """
        _title = ""
        if new_title and isinstance(new_title, str):
            _title = f"{new_title}: "
        if new_description:
            ui_qt_utils.update_formatted_label(
                target_label=self.description,
                text=_title,
                text_size=3,
                text_color="grey",
                output_text=new_description,
                output_size=3,
                output_color="white",
                overall_alignment="center",
            )

    def moveEvent(self, event):
        """Updates scaled description sizing after the window moves.

        Args:
            event (QMoveEvent): Qt move event.
        """
        """
        Move Event, called when the window is moved (must use this name "moveEvent").
        Updates the maximum size of the description according to the scale factor of the current screen.
        """
        default_maximum_height_description = 20
        scale_factor = 1  # Default scale factor if no screen is found

        if ui_qt.IS_PYSIDE6:
            screen = ui_qt.QtGui.QGuiApplication.screenAt(self.mapToGlobal(self.rect().center()))
            if screen:
                scale_factor = screen.devicePixelRatio()
        else:
            desktop = ui_qt.QtWidgets.QDesktopWidget()
            screen_number = desktop.screenNumber(self)
            scale_factor = ui_qt_utils.get_screen_dpi_scale(screen_number)

        # Apply the scale factor to set the maximum height
        self.description.setMaximumHeight(default_maximum_height_description * scale_factor)


if __name__ == "__main__":
    with ui_qt_utils.QtApplicationContext():
        window = MeshLibraryView()
        mocked_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.mesh_library_base)
        window.add_item_view_library(item_name="curve_one", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.mesh_library_user))
        window.add_item_view_library(item_name="curve_two", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.mesh_library_param))
        for index in range(1, 101):
            window.add_item_view_library(
                item_name=f"curve_with_a_very_long_name_for_testing_ui_{index}", icon=mocked_icon
            )
        window.show()
