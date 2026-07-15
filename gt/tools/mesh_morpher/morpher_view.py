"""Mesh Morpher View."""

import gt.ui.resource_library as ui_res_lib
import gt.core.session as core_session
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MorpherView(metaclass=ui_qt_utils.MayaWindowMeta):
    """Main interface for configuring and running mesh morph definitions."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the Mesh Morpher view.

        Args:
            parent (QWidget, optional): Parent widget.
            controller (MorpherController, optional): Controller reference.
            version (str, optional): Version displayed in the window title.
        """
        super().__init__(parent=parent)
        self.controller = controller

        self.new_rbf_cache_btn = None
        self.rbf_list_widget = None
        self.rbf_container_layout = None
        self.rbf_container = None
        self.subject_mesh_list = None
        self.subject_get_button = None
        self.subject_delete_button = None
        self.subject_rename_button = None
        self.post_tab_widget = None
        self.import_button = None
        self.export_button = None
        self.generate_button = None

        window_title = "Mesh Morpher"
        if version:
            window_title += " - (v{})".format(version)
        self.setWindowTitle(window_title)
        self.setMinimumSize(760, 560)
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_mesh_morpher))
        self.setStyleSheet(self._build_stylesheet())
        self._build_layout()

        ui_qt_utils.resize_to_screen(self, height_percentage=62, width_percentage=48)
        ui_qt_utils.center_window(self)

    def _build_layout(self):
        """Builds the complete interface layout."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 14)
        main_layout.setSpacing(10)
        main_layout.addWidget(self._build_header())

        content_splitter = ui_qt.QtWidgets.QSplitter()
        content_splitter.setObjectName("contentSplitter")
        content_splitter.addWidget(self._build_setup_panel())
        content_splitter.addWidget(self._build_post_process_panel())
        content_splitter.setStretchFactor(0, 2)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([330, 500])
        main_layout.addWidget(content_splitter, 1)
        main_layout.addWidget(self._build_run_panel())

    def _build_header(self):
        """Builds the title, workflow description, and file actions.

        Returns:
            QWidget: Header widget.
        """
        header = ui_qt.QtWidgets.QFrame()
        header.setObjectName("headerCard")
        layout = ui_qt.QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(10)

        text_layout = ui_qt.QtWidgets.QVBoxLayout()
        text_layout.setSpacing(2)
        title = ui_qt.QtWidgets.QLabel("Mesh Morpher")
        title.setObjectName("toolTitle")
        description = ui_qt.QtWidgets.QLabel(
            "Choose morph caches, add the meshes to reshape, then configure optional post-processing."
        )
        description.setObjectName("toolDescription")
        description.setWordWrap(True)
        text_layout.addWidget(title)
        text_layout.addWidget(description)
        layout.addLayout(text_layout, 1)

        self.import_button = self._create_button(
            "Load Definitions", ui_res_lib.Icon.ui_open, "Load subject definitions from a JSON file."
        )
        self.export_button = self._create_button(
            "Save Definitions", ui_res_lib.Icon.ui_save, "Save all current subject definitions to a JSON file."
        )
        layout.addWidget(self.import_button)
        layout.addWidget(self.export_button)
        return header

    def _build_setup_panel(self):
        """Builds the cache and subject setup panel.

        Returns:
            QWidget: Setup panel.
        """
        panel = ui_qt.QtWidgets.QWidget()
        panel.setMinimumWidth(300)
        layout = ui_qt.QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_cache_card(), 1)
        layout.addWidget(self._build_subject_card(), 1)
        return panel

    def _build_cache_card(self):
        """Builds the morph-cache selection card.

        Returns:
            QGroupBox: Cache card.
        """
        cache_group = ui_qt.QtWidgets.QGroupBox("1. Morph Caches")
        cache_group.setToolTip("Checked cache files are applied to the selected subject definition.")
        layout = ui_qt.QtWidgets.QVBoxLayout(cache_group)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(6)
        hint = self._create_hint_label(
            "Select one or more RBF caches. Creating a cache uses the source and target meshes selected in Maya."
        )
        layout.addWidget(hint)

        self.rbf_list_widget = ui_qt.QtWidgets.QScrollArea()
        self.rbf_list_widget.setObjectName("cacheList")
        self.rbf_list_widget.setWidgetResizable(True)
        self.rbf_list_widget.setMinimumHeight(110)
        self.rbf_container = ui_qt.QtWidgets.QWidget()
        self.rbf_container_layout = ui_qt.QtWidgets.QVBoxLayout(self.rbf_container)
        self.rbf_container_layout.setContentsMargins(8, 6, 8, 6)
        self.rbf_container_layout.setSpacing(4)
        self.rbf_container_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.rbf_list_widget.setWidget(self.rbf_container)
        layout.addWidget(self.rbf_list_widget, 1)

        self.new_rbf_cache_btn = self._create_button(
            "Create Cache from Selection...",
            ui_res_lib.Icon.ui_add,
            "Create an RBF morph cache from the source and target meshes selected in Maya.",
        )
        layout.addWidget(self.new_rbf_cache_btn)
        return cache_group

    def _build_subject_card(self):
        """Builds the subject-mesh card.

        Returns:
            QGroupBox: Subject card.
        """
        subject_group = ui_qt.QtWidgets.QGroupBox("2. Subject Meshes")
        layout = ui_qt.QtWidgets.QVBoxLayout(subject_group)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(6)
        layout.addWidget(
            self._create_hint_label(
                "Add clean meshes with matching topology. Checked subjects are included when Generate is run."
            )
        )

        self.subject_mesh_list = ui_qt.QtWidgets.QListWidget()
        self.subject_mesh_list.setObjectName("subjectList")
        self.subject_mesh_list.setSelectionMode(ui_qt.QtLib.SelectionMode.SingleSelection)
        self.subject_mesh_list.setMinimumHeight(110)
        self.subject_mesh_list.setSpacing(1)
        self.subject_mesh_list.setAlternatingRowColors(True)
        self.subject_mesh_list.setToolTip(
            "Select a subject to edit its post-processing settings. Double-click a name to edit it."
        )
        layout.addWidget(self.subject_mesh_list, 1)

        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        button_layout.setSpacing(6)
        self.subject_get_button = self._create_button(
            "Add Selected", ui_res_lib.Icon.ui_add, "Add selected Maya mesh transforms as subjects."
        )
        self.subject_delete_button = self._create_button(
            "Remove", ui_res_lib.Icon.ui_delete, "Remove the selected subject definition from the list."
        )
        button_layout.addWidget(self.subject_get_button, 1)
        button_layout.addWidget(self.subject_delete_button)
        layout.addLayout(button_layout)

        rename_hint = ui_qt.QtWidgets.QLabel("Tip: Double-click a subject name to edit it.")
        rename_hint.setObjectName("microHint")
        layout.addWidget(rename_hint)
        return subject_group

    def _build_post_process_panel(self):
        """Builds the selected-subject post-processing panel.

        Returns:
            QGroupBox: Post-processing panel.
        """
        post_group = ui_qt.QtWidgets.QGroupBox("3. Post-Processing for Selected Subject")
        post_group.setMinimumWidth(390)
        layout = ui_qt.QtWidgets.QVBoxLayout(post_group)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(7)
        layout.addWidget(
            self._create_hint_label(
                "These settings belong to the highlighted subject. Use the tabs to control cleanup and output behavior."
            )
        )
        self.post_tab_widget = ui_qt.QtWidgets.QTabWidget()
        self.post_tab_widget.setObjectName("postProcessTabs")
        self.post_tab_widget.setDocumentMode(True)
        self.post_tab_widget.setMinimumHeight(300)
        layout.addWidget(self.post_tab_widget, 1)
        return post_group

    def _build_run_panel(self):
        """Builds the final generation action panel.

        Returns:
            QWidget: Run panel.
        """
        panel = ui_qt.QtWidgets.QFrame()
        panel.setObjectName("runCard")
        layout = ui_qt.QtWidgets.QHBoxLayout(panel)
        layout.setContentsMargins(12, 9, 9, 9)
        layout.setSpacing(12)
        text_layout = ui_qt.QtWidgets.QVBoxLayout()
        text_layout.setSpacing(1)
        title = ui_qt.QtWidgets.QLabel("Ready to reshape?")
        title.setObjectName("runTitle")
        description = ui_qt.QtWidgets.QLabel(
            "The checked caches and enabled post-processing settings will be applied to every checked subject."
        )
        description.setObjectName("toolDescription")
        description.setWordWrap(True)
        text_layout.addWidget(title)
        text_layout.addWidget(description)
        layout.addLayout(text_layout, 1)
        self.generate_button = self._create_button(
            "Generate Reshaped Meshes",
            ui_res_lib.Icon.ui_progress,
            "Generate output meshes for all checked subjects.",
        )
        self.generate_button.setObjectName("generateButton")
        self.generate_button.setMinimumHeight(42)
        self.generate_button.setMinimumWidth(220)
        layout.addWidget(self.generate_button)
        return panel

    @staticmethod
    def _create_hint_label(text):
        """Creates a wrapping explanatory label.

        Args:
            text (str): Hint text.

        Returns:
            QLabel: Created hint label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("hintLabel")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_button(text, icon, tooltip):
        """Creates a labeled action button.

        Args:
            text (str): Button text.
            icon (str): Icon path.
            tooltip (str): Button tooltip.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(text)
        button.setIcon(ui_qt.QtGui.QIcon(icon))
        button.setToolTip(tooltip)
        button.setMinimumHeight(30)
        return button

    @staticmethod
    def _build_stylesheet():
        """Builds the Mesh Morpher stylesheet.

        Returns:
            str: Combined repository and tool-specific stylesheet.
        """
        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.combobox_base
        stylesheet += ui_res_lib.Stylesheet.tree_widget_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        stylesheet += ui_res_lib.Stylesheet.table_widget_base
        stylesheet += ui_res_lib.Stylesheet.checkbox_base
        stylesheet += ui_res_lib.Stylesheet.line_edit_base
        stylesheet += ui_res_lib.Stylesheet.spin_box_base
        stylesheet += ui_res_lib.Stylesheet.slider_base
        stylesheet += ui_res_lib.Stylesheet.tab_widget_base
        if not core_session.is_script_in_interactive_maya():
            stylesheet += ui_res_lib.Stylesheet.menu_base
        stylesheet += """
            QFrame#headerCard, QFrame#runCard {
                background-color: #3b3d40; border: 1px solid #505257; border-radius: 4px;
            }
            QLabel#toolTitle { color: #f0f0f0; font-size: 18px; font-weight: bold; }
            QLabel#toolDescription, QLabel#hintLabel { color: #aeb1b5; }
            QLabel#microHint { color: #85898e; font-size: 10px; font-style: italic; }
            QLabel#runTitle { color: #e5e5e5; font-weight: bold; }
            QGroupBox {
                border: 1px solid #505257; border-radius: 4px; margin-top: 9px; font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 9px; padding: 0 5px; color: #c9cbce; }
            QScrollArea#cacheList, QListWidget#subjectList {
                background-color: #292b2e; border: 1px solid #44474b; border-radius: 2px;
            }
            QPushButton#generateButton {
                background-color: #4f7f86; color: #ffffff; border: 1px solid #65969d;
                border-radius: 3px; font-weight: bold; padding: 6px 14px;
            }
            QPushButton#generateButton:hover { background-color: #5d9098; }
            QPushButton#generateButton:pressed { background-color: #3f6c72; }
        """
        return stylesheet

    def add_item_subject_list(self, subject_name):
        """Adds a subject item unless an item with the same name exists.

        Args:
            subject_name (str): Mesh subject name.

        Returns:
            QListWidgetItem: Existing or newly created subject item.
        """
        for index in range(self.subject_mesh_list.count()):
            item = self.subject_mesh_list.item(index)
            if item.text() == subject_name:
                return item

        subject_item = ui_qt.QtWidgets.QListWidgetItem(subject_name)
        if ui_qt.IS_PYSIDE6:
            editable_flag = ui_qt.QtCore.Qt.ItemFlag.ItemIsEditable
        else:
            editable_flag = ui_qt.QtCore.Qt.ItemIsEditable
        subject_item.setFlags(subject_item.flags() | editable_flag)
        subject_item.setSizeHint(ui_qt.QtCore.QSize(0, 27))
        subject_item.setCheckState(ui_qt.QtLib.CheckState.Checked)
        self.subject_mesh_list.addItem(subject_item)
        return subject_item

    def delete_item_subject_list(self, subject_name=None):
        """Deletes a named subject or the selected subject.

        Args:
            subject_name (str, optional): Subject to delete. Selection is used when omitted.

        Returns:
            str or None: Deleted subject name.
        """
        item_to_delete = None
        if subject_name:
            for index in range(self.subject_mesh_list.count()):
                item = self.subject_mesh_list.item(index)
                if item.text() == subject_name:
                    item_to_delete = item
                    break
        else:
            selected_items = self.subject_mesh_list.selectedItems()
            if not selected_items:
                logger.debug("Nothing selected. Delete item skipped.")
                return None
            item_to_delete = selected_items[0]
            subject_name = item_to_delete.text()
        if item_to_delete:
            self.subject_mesh_list.takeItem(self.subject_mesh_list.row(item_to_delete))
            return subject_name
        return None

    def select_last_item_subject_list(self):
        """Selects the last subject item."""
        self.subject_mesh_list.blockSignals(True)
        for index in range(self.subject_mesh_list.count()):
            self.subject_mesh_list.item(index).setSelected(index == self.subject_mesh_list.count() - 1)
        self.subject_mesh_list.blockSignals(False)

    def get_checked_meshes_subject_list(self):
        """Gets subject names enabled for generation.

        Returns:
            list: Checked subject names.
        """
        subject_names = []
        for index in range(self.subject_mesh_list.count()):
            item = self.subject_mesh_list.item(index)
            if item.checkState() == ui_qt.QtLib.CheckState.Checked:
                subject_names.append(item.text())
        return subject_names


if __name__ == "__main__":
    with ui_qt_utils.QtApplicationContext():
        window = MorpherView()
        window.show()
