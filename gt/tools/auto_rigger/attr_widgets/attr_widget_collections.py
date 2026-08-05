"""
Auto Rigger Collections Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleCollections(AttrWidget):
    """
    An attribute widget for managing rig collections, including support for
    dynamic query-based collections.

    This widget ensures that module data is committed immediately upon any UI change
    and when the widget is instructed to save its data (e.g., when switching modules)
    to prevent data loss.
    """

    def __init__(self, parent=None, *args, **kwargs):
        """
        Initializes the attribute widget for the collections module.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            *args: Additional positional arguments for the base class.
            **kwargs: Additional keyword arguments for the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        # Collections Section
        self.add_widget_separator_line(label_text="Collections Data")

        # "Add Collection" Button
        add_collection_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(add_collection_button_layout)
        add_collection_button = ui_qt.QtWidgets.QPushButton("Add Collection")
        add_collection_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_collection_button.setToolTip("Adds a new, empty collection.")
        add_collection_button.clicked.connect(self.on_add_collection_clicked)
        add_collection_button_layout.addWidget(add_collection_button)

        # Scroll Area for Collection Widgets
        self.collection_scroll_area = ui_qt.QtWidgets.QScrollArea()
        self.collection_scroll_area.setWidgetResizable(True)
        self.collection_scroll_area.setMinimumHeight(220)
        self.collection_container = ui_qt.QtWidgets.QWidget()
        self.collection_vertical_layout = ui_qt.QtWidgets.QVBoxLayout(self.collection_container)
        self.collection_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.collection_vertical_layout.setSpacing(8)
        self.collection_vertical_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.collection_scroll_area.setWidget(self.collection_container)
        self.content_layout.addWidget(self.collection_scroll_area)

        self.refresh_current_widgets()

        # Action Buttons
        write_collections_btn = ui_qt.QtWidgets.QPushButton("Write Collections Data To Current Rig")
        write_collections_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        clear_collections_btn = ui_qt.QtWidgets.QPushButton("Clear Collections Data from Current Rig")
        clear_collections_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))

        _layout = ui_qt.QtWidgets.QHBoxLayout(self)
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.addWidget(write_collections_btn)
        _layout.addWidget(clear_collections_btn)
        self.content_layout.addLayout(_layout)

        write_collections_btn.clicked.connect(self._write_collections_data)
        clear_collections_btn.clicked.connect(self._clear_collections_data)

    def commit_data(self):
        """
        Overrides the base class method to ensure data is committed
        when the widget is instructed to save (e.g., when switching modules).
        """
        self.commit_collection_data_to_module()

    def add_collection_widget(self, collection_data, query_expression=None):
        """
        Creates and adds a widget for managing a single collection.

        Args:
            collection_data (dict): A dictionary representing one collection.
            query_expression (tuple[str, bool, bool] or None, optional):
                                         It should be (expression_string, is_collection_query, is_joints_only).
                                         If provided, the expression UI is shown. Defaults to None.
        """
        collection_name = list(collection_data.keys())[0]
        collection_objects = list(collection_data.values())[0]
        is_query_mode = query_expression is not None
        query_text = query_expression[0] if is_query_mode else ""
        is_collection_query = query_expression[1] if is_query_mode else False

        default_joints_only = True
        if is_query_mode:
            is_joints_only = query_expression[2] if len(query_expression) > 2 else default_joints_only
        else:
            is_joints_only = default_joints_only

        collection_frame = ui_qt.QtWidgets.QFrame()
        collection_frame.setFrameShape(ui_qt.QtWidgets.QFrame.StyledPanel)
        main_collection_layout = ui_qt.QtWidgets.QVBoxLayout(collection_frame)

        # Top Layout: Name, Query Checkbox, and Delete button
        top_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_label = ui_qt.QtWidgets.QLabel("Collection Name:")
        name_line_edit = ui_qt_utils.ConfirmableQLineEdit(collection_name)
        name_line_edit.setObjectName("collection_name_field")

        # Query Expression Checkbox
        query_checkbox = ui_qt.QtWidgets.QCheckBox("Query Expression")
        query_checkbox.setChecked(is_query_mode)
        query_checkbox.setObjectName("query_checkbox")
        query_checkbox.setToolTip(
            "If checked, this collection is dynamically populated using a search "
            "expression instead of a static object list."
        )

        delete_collection_button = ui_qt.QtWidgets.QPushButton()
        delete_collection_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_collection_button.setToolTip("Deletes this entire collection.")

        # Layout for the top row
        top_layout.addWidget(name_label)
        top_layout.addWidget(name_line_edit, 1)
        top_layout.addWidget(query_checkbox)
        top_layout.addWidget(delete_collection_button)

        # Bottom Layout: Static Objects (Default)
        self.static_objects_widget = ui_qt.QtWidgets.QWidget()
        static_objects_layout = ui_qt.QtWidgets.QHBoxLayout(self.static_objects_widget)
        static_objects_layout.setContentsMargins(0, 0, 0, 0)
        objects_label = ui_qt.QtWidgets.QLabel("Objects:")
        objects_line_edit = ui_qt_utils.ConfirmableQLineEdit(", ".join(collection_objects))
        objects_line_edit.setObjectName("objects_list_field")
        objects_line_edit.setPlaceholderText("objOne, objTwo, ...")
        add_selection_button = ui_qt.QtWidgets.QPushButton("Add Selection")
        add_selection_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_cursor))
        add_selection_button.setToolTip("Populates the field with the current Maya selection.")
        static_objects_layout.addWidget(objects_label)
        static_objects_layout.addWidget(objects_line_edit)
        static_objects_layout.addWidget(add_selection_button)

        # Expression Widget (Query Mode)
        self.query_expression_widget = ui_qt.QtWidgets.QWidget()
        query_expression_layout = ui_qt.QtWidgets.QHBoxLayout(self.query_expression_widget)
        query_expression_layout.setContentsMargins(0, 0, 0, 0)
        expression_label = ui_qt.QtWidgets.QLabel("Expression:")
        expression_line_edit = ui_qt_utils.ConfirmableQLineEdit(query_text)
        expression_line_edit.setObjectName("expression_field")
        expression_line_edit.setPlaceholderText("*_JNT, |path|to|geo, etc.")

        # Joints Only Checkbox
        joints_only_checkbox = ui_qt.QtWidgets.QCheckBox("Joints Only")
        joints_only_checkbox.setChecked(is_joints_only)
        joints_only_checkbox.setObjectName("is_joints_only_checkbox")
        joints_only_checkbox.setToolTip("If checked, the Maya search is restricted only to joint type elements.")

        # Query Type Checkbox (Collection Search)
        collection_query_checkbox = ui_qt.QtWidgets.QCheckBox("Collection Search")
        collection_query_checkbox.setChecked(is_collection_query)
        collection_query_checkbox.setObjectName("is_collection_query_checkbox")
        collection_query_checkbox.setToolTip(
            "If checked, the expression is run against existing collections (e.g., 'mesh_collection'), "
            "otherwise it is run as a standard Maya `cmds.ls` query (e.g., '*_GEO')."
        )

        # Update Expression Layout
        query_expression_layout.addWidget(expression_label)
        query_expression_layout.addWidget(expression_line_edit)
        query_expression_layout.addWidget(joints_only_checkbox)
        query_expression_layout.addWidget(collection_query_checkbox)

        self.query_expression_widget.setVisible(is_query_mode)
        self.static_objects_widget.setVisible(not is_query_mode)

        # Assemble Layout
        main_collection_layout.addLayout(top_layout)
        main_collection_layout.addWidget(self.static_objects_widget)
        main_collection_layout.addWidget(self.query_expression_widget)
        self.collection_vertical_layout.addWidget(collection_frame)

        # Connections (Crucial for immediate commit)
        name_line_edit.editingFinished.connect(self.commit_collection_data_to_module)
        objects_line_edit.editingFinished.connect(self.commit_collection_data_to_module)
        expression_line_edit.editingFinished.connect(self.commit_collection_data_to_module)

        # Ensure checkbox state changes commit immediately
        joints_only_checkbox.toggled.connect(self.commit_collection_data_to_module)
        collection_query_checkbox.toggled.connect(self.commit_collection_data_to_module)

        # Query Checkbox Toggling Logic and Commit
        toggle_func = partial(
            self.on_query_checkbox_toggled,
            static_widget=self.static_objects_widget,
            query_widget=self.query_expression_widget,
        )
        query_checkbox.toggled.connect(toggle_func)
        query_checkbox.toggled.connect(self.commit_collection_data_to_module)

        delete_func = partial(self.on_delete_collection_widget_clicked, to_delete=collection_frame)
        delete_collection_button.clicked.connect(delete_func)
        add_selection_func = partial(self.on_add_selection_clicked, target_field=objects_line_edit)
        add_selection_button.clicked.connect(add_selection_func)

    def refresh_current_widgets(self):
        """
        Rebuilds the UI to match the module's current collection data.
        """
        self._clear_layout(self.collection_vertical_layout)

        # Ensure data lists exist on the module
        if not hasattr(self.module, "collection_dicts"):
            self.module.collection_dicts = []
        # Note: self.module.collection_private_keys is no longer managed in the UI
        if not hasattr(self.module, "collection_expressions"):
            self.module.collection_expressions = []

        # Convert expression list for quick lookup: {name: (expression, is_collection_query, is_joints_only)}
        expression_lookup = {}
        default_joints_only = True

        for item in self.module.collection_expressions:
            is_joints_only = item.get("is_joints_only", default_joints_only)
            expression_lookup[item["name"]] = (item["expression"], item["is_collection_query"], is_joints_only)

        # Note: private_keys retrieval removed

        for collection_data in self.module.collection_dicts:
            collection_name = list(collection_data.keys())[0]

            # Note: is_private check removed
            query_expression = expression_lookup.get(collection_name)

            self.add_collection_widget(collection_data=collection_data, query_expression=query_expression)

    def get_collection_data_from_layout(self):
        """
        Extracts all collection data and query expressions from the UI widgets.

        Returns:
            tuple[list[dict], list[str], list[dict]]: A tuple containing:
                - A list of dictionaries representing the collections (name: [objects]).
                - An empty list (legacy compatibility, previously private keys).
                - A list of dictionaries for query expressions.
                  Example: [{"name": "coll_name", "expression": "str", "is_collection_query": bool, "is_joints_only": bool}]
        """
        new_collection_dicts = []
        # The list for private keys is kept but remains empty to match the expected return signature.
        new_private_keys = []
        new_collection_expressions = []

        for index in range(self.collection_vertical_layout.count()):
            collection_frame = self.collection_vertical_layout.itemAt(index).widget()
            if not collection_frame:
                continue

            name_field = collection_frame.findChild(ui_qt.QtWidgets.QLineEdit, "collection_name_field")
            collection_name = name_field.text() if name_field else "unknown_collection"

            # Find all relevant UI elements
            query_checkbox = collection_frame.findChild(ui_qt.QtWidgets.QCheckBox, "query_checkbox")

            objects_field = collection_frame.findChild(ui_qt.QtWidgets.QLineEdit, "objects_list_field")
            expression_field = collection_frame.findChild(ui_qt.QtWidgets.QLineEdit, "expression_field")
            collection_query_checkbox = collection_frame.findChild(
                ui_qt.QtWidgets.QCheckBox, "is_collection_query_checkbox"
            )
            joints_only_checkbox = collection_frame.findChild(ui_qt.QtWidgets.QCheckBox, "is_joints_only_checkbox")

            # 1. Get Query Expression Status and Data
            is_query_mode = query_checkbox and query_checkbox.isChecked()

            if is_query_mode and expression_field and collection_query_checkbox and joints_only_checkbox:
                expression = expression_field.text().strip()
                is_collection_query = collection_query_checkbox.isChecked()
                is_joints_only = joints_only_checkbox.isChecked()

                # Append the expression data regardless of whether the expression string is empty.
                new_collection_expressions.append(
                    {
                        "name": collection_name,
                        "expression": expression,
                        "is_collection_query": is_collection_query,
                        "is_joints_only": is_joints_only,
                    }
                )

                # The collection_dicts entry will have an empty list of objects when in query mode
                object_names = []

            # 2. Get Static Objects (only if NOT in query mode)
            else:
                if objects_field:
                    objects_text = objects_field.text()
                    # Split by comma, strip whitespace, and remove empty entries
                    object_names = [item.strip() for item in objects_text.split(",") if item.strip()]
                else:
                    object_names = []

            new_collection_dicts.append({collection_name: object_names})

        return new_collection_dicts, new_private_keys, new_collection_expressions

    def commit_collection_data_to_module(self):
        """
        Writes the current collection data, private keys (empty), and expressions from
        the UI to the module instance.
        """
        (new_collection_dicts, new_private_keys, new_collection_expressions) = self.get_collection_data_from_layout()

        self.module.collection_dicts = new_collection_dicts
        # Set collection_private_keys to the empty list returned by get_collection_data_from_layout
        self.module.collection_private_keys = new_private_keys
        self.module.collection_expressions = new_collection_expressions

    def on_add_collection_clicked(self):
        """
        Handles adding a new, empty collection widget.
        """
        # We only need the names from the current layout for conflict checking
        existing_names = [list(d.keys())[0] for d in self.get_collection_data_from_layout()[0]]
        new_name = "collection"
        counter = 1
        while new_name in existing_names:
            new_name = f"collection_{counter}"
            counter += 1

        self.add_collection_widget(collection_data={new_name: []}, query_expression=None)
        self.commit_collection_data_to_module()

    def on_query_checkbox_toggled(self, is_checked, static_widget, query_widget):
        """
        Handles the visibility toggle for the static objects vs. query expression widgets.

        Args:
            is_checked (bool): True if the query checkbox is checked.
            static_widget (QWidget): The widget containing the 'Objects:' field.
            query_widget (QWidget): The widget containing the 'Expression:' field.
        """
        static_widget.setVisible(not is_checked)
        query_widget.setVisible(is_checked)

    def on_delete_collection_widget_clicked(self, to_delete):
        """
        Handles the deletion of a collection widget.

        Args:
            to_delete (QWidget): The collection frame widget to be removed.
        """
        self._remove_widget(to_delete)
        self.commit_collection_data_to_module()

    def on_add_selection_clicked(self, target_field):
        """
        Gets the current Maya selection and populates the target text field.

        Args:
            target_field (QLineEdit): The line edit widget to populate.
        """
        import gt.core.selection as core_sel

        selection = core_sel.ensure_selection_count(
            selection_limit=None,
            require_exact_count=False,
        )

        target_field.setText(", ".join(selection))
        self.commit_collection_data_to_module()

    @staticmethod
    def _clear_layout(layout):
        """
        Removes all widgets from a given layout.

        Args:
            layout (QLayout): The layout to be cleared.
        """
        if not layout:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    @staticmethod
    def _remove_widget(widget):
        """
        Removes a Qt widget from its parent and schedules it for deletion.

        Args:
            widget (QWidget): The widget to remove and delete.
        """
        if widget:
            widget.setParent(None)
            widget.deleteLater()

    def _write_collections_data(self):
        """
        Executes the model's setup_collections method to write data to the rig.
        """
        # The first thing we must do here is commit the current UI state to the module
        self.commit_collection_data_to_module()

        root_group = tools_rig_utils.find_root_group_rig()
        if not root_group:
            # Assuming logger and tools_rig_utils are imported/available
            logger.warning(f"No rig detected in the scene. Unable to apply collections data.")
            return
        self.module.setup_collections()
        logger.info("Collection data was written to the current rig.")

    def _clear_collections_data(self):
        """
        Finds and clears the collections data attribute from the rig's root node.
        """
        self.module.clear_collections()
