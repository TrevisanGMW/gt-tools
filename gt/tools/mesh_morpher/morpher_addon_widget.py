"""
Mesh Morpher Addon Widgets
"""

import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
from functools import partial
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TabWidget(ui_qt.QtWidgets.QWidget):
    """
    Base Widget for managing addons in a tab.
    """

    def __init__(self, parent=None, addon=None, definition=None, *args, **kwargs):
        """
        Initialize the AttrWidget.

        Args:
            parent (QWidget): The parent widget.
            addon (MeshMorpherAddon): The addon associated with this widget.
            definition (MeshMorpherDefinition): The definition associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)

        # Basic Variables
        self.addon = addon
        self.definition = definition

        # Content Layout
        self.content_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        # Create Layout
        self.scroll_content_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        self.scroll_content_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.scroll_content_layout.addLayout(self.content_layout)

        self.setLayout(self.content_layout)

    # ---------------------------------------------- Base Layers ----------------------------------------------
    def refresh_layers(self):
        """Empty function to be overwritten when refreshing layers"""
        ...

    def delete_layer(self, index):
        """
        Removes a layer from self.addon.layers and updates the UI.

        Args:
            index (int): The index of the layer to remove.
        """
        if 0 <= index < len(self.addon.layers):
            deleted_layer = self.addon.layers.pop(index)
            self.refresh_layers()  # Refresh the UI

    def _clear_layer_layout(self, layout):
        """
        Recursively clears all widgets and sub-layouts inside the given layout.
        Args:
            layout (QLayout): The layout to clear.
        """
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layer_layout(item.layout())

    def add_layer(self):
        """
        Adds a new empty layer and refreshes the UI.
        """
        self.addon.add_default_layer()
        self.refresh_layers()  # Refresh the UI

    def update_layer_name(self, index, new_name):
        """
        Updates the 'name' field of the layer dictionary at the given index.
        Args:
            index (int): The index of the layer to update.
            new_name (str): The new name to assign to the layer.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["name"] = new_name

    def update_layer_vertices(self, index, new_vertices):
        """
        Updates the 'vertices' field of the layer dictionary at the given index.
        Args:
            index (int): The index of the layer to update.
            new_vertices (list): The new vertices data to assign to the layer.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["vertices"] = new_vertices

    def update_layer_anchor(self, index, vertex):
        """
        Updates the 'vertices' field of the layer dictionary at the given index.
        Args:
            index (int): The index of the layer to update.
            vertex (int): The vertex to assign as anchor.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["anchor"] = vertex

    def select_layer_vertices(self, index):
        """
        Select vertices from the specified layer using the stored vertex data.

        Attempts to unpack and select the vertices described in the layer's 'vertices' field.

        Args:
            index (int): The index of the layer whose vertices should be selected.
        """
        if 0 <= index < len(self.addon.layers):
            packed_vertices = self.addon.layers[index].get("vertices")
            subject_mesh = self.definition.get_subject_mesh()
            vertices = self.addon.unpack_vertices(mesh_name=subject_mesh, vertices_string=packed_vertices)
            import maya.cmds as cmds

            cmds.select(vertices)

    def select_layer_anchor(self, index):
        """
        Select the vertex picked as anchor point from the specified layer using the stored anchor data.

        Args:
            index (int): The index of the layer whose vertices should be selected.
        """
        if 0 <= index < len(self.addon.layers):
            anchor = self.addon.layers[index].get("anchor")
            subject_mesh = self.definition.get_subject_mesh()
            import maya.cmds as cmds

            try:
                cmds.select(f"{subject_mesh}.vtx[{str(anchor)}]")
            except Exception:
                logger.warning(f"Selected mesh does not have vertex '{str(anchor)}'.")

    def update_vertices_field_with_selection(self, index):
        """
        Update the 'vertices' field of the specified layer with the currently selected vertices.
        Args:
            index (int): The index of the layer to update.
        """
        packed_vertices = self.addon.get_packed_vertices()
        if 0 <= index < len(self.addon.layers) and packed_vertices:
            self.addon.layers[index]["vertices"] = packed_vertices
        self.refresh_layers()

    def update_anchor_field_with_selection(self, index):
        """
        Update the anchor field of the specified layer with the currently selected vertex.
        Args:
            index (int): The index of the layer to update.
        """
        import maya.cmds as cmds

        sel = cmds.ls(selection=True, flatten=True)
        if sel:
            vtx_index = int(sel[-1].split(".vtx[")[1][:-1])
            self.addon.layers[index]["anchor"] = vtx_index
        self.refresh_layers()


class TabWidgetDeltaMush(TabWidget):
    def __init__(self, parent=None, addon=None, definition=None, *args, **kwargs):
        """
        Initialize the AttrWidget.

        Args:
            parent (QWidget): The parent widget.
            addon (MeshMorpherAddon): The addon associated with this widget.
            definition (MeshMorpherDefinition): The definition associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, addon=addon, definition=definition, *args, **kwargs)
        # Add Button
        self.add_layer_button = ui_qt.QtWidgets.QPushButton()
        self.add_layer_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        self.add_layer_button.clicked.connect(self.add_layer)
        self.content_layout.addWidget(self.add_layer_button)
        # Delta Mush Layers
        self.delta_mush_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.addLayout(self.delta_mush_layout)
        self.refresh_layers()

    def refresh_layers(self):
        """
        Creates UI elements for each layer, including name fields and delete buttons.
        """
        # Clear layout before recreating UI (avoids duplicates)
        while self.delta_mush_layout.count():
            item = self.delta_mush_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layer_layout(item.layout())

        for index, layer in enumerate(self.addon.layers):
            layer_layout = ui_qt.QtWidgets.QVBoxLayout()

            # Layer Name
            name_and_delete_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Name:")
            layer_field = ui_qt.QtWidgets.QLineEdit(layer.get("name", ""))
            layer_field.textChanged.connect(partial(self.update_layer_name, index))
            name_and_delete_layout.addWidget(label)
            name_and_delete_layout.addWidget(layer_field)

            # Delete Button
            delete_button = ui_qt.QtWidgets.QPushButton()
            delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_button.clicked.connect(partial(self.delete_layer, index))
            name_and_delete_layout.addWidget(delete_button)
            layer_layout.addLayout(name_and_delete_layout)

            # Vertices
            vertices_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Vertices:")
            layer_field = ui_qt.QtWidgets.QLineEdit(layer.get("vertices", ""))
            layer_field.textChanged.connect(partial(self.update_layer_vertices, index))
            vertices_layout.addWidget(label)
            vertices_layout.addWidget(layer_field)

            # Get Button
            get_vertices_button = ui_qt.QtWidgets.QPushButton("GET")
            get_vertices_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            get_vertices_button.clicked.connect(partial(self.update_vertices_field_with_selection, index))
            select_vertices_button = ui_qt.QtWidgets.QPushButton("SELECT")
            select_vertices_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            select_vertices_button.clicked.connect(partial(self.select_layer_vertices, index))
            vertices_layout.addWidget(get_vertices_button)
            vertices_layout.addWidget(select_vertices_button)
            layer_layout.addLayout(vertices_layout)

            # Smoothing Iterations
            si_layout = ui_qt.QtWidgets.QHBoxLayout()
            si_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            label = ui_qt.QtWidgets.QLabel(f"Smoothing Iterations:")
            si_slider = ui_qt_utils.QIntSlider(ui_qt.QtLib.Orientation.Horizontal)
            spinbox = ui_qt.QtWidgets.QSpinBox()
            si_slider.link_spin_box(spinbox)
            si_slider.set_int_range(min_int=0, max_int=100)
            si_slider.set_int_value(layer.get("smoothingIterations", 10))
            tooltip = "Number of times the smoothing algorithm is run."
            si_slider.intValueChanged.connect(partial(self.update_layer_smoothing_iterations, index))
            si_slider.setToolTip(tooltip)
            label.setToolTip(tooltip)
            spinbox.setToolTip(tooltip)
            si_layout.addWidget(label)
            si_layout.addWidget(si_slider)
            si_layout.addWidget(spinbox)
            layer_layout.addLayout(si_layout)

            # Distance Weight
            dw_layout = ui_qt.QtWidgets.QHBoxLayout()
            dw_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            label = ui_qt.QtWidgets.QLabel(f"Distance Weight:")
            dw_slider = ui_qt_utils.QDoubleSlider(ui_qt.QtLib.Orientation.Horizontal)
            spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
            spinbox.setDecimals(3)
            dw_slider.link_spin_box(spinbox)
            dw_slider.set_double_range(min_double=0, max_double=1)
            dw_slider.set_double_value(layer.get("distanceWeight", 1))
            dw_slider.doubleValueChanged.connect(partial(self.update_layer_distance_weight, index))
            tooltip = 'Distance between vertices when calculating the "mush" deformation.'
            dw_slider.setToolTip(tooltip)
            label.setToolTip(tooltip)
            spinbox.setToolTip(tooltip)
            dw_layout.addWidget(label)
            dw_layout.addWidget(dw_slider)
            dw_layout.addWidget(spinbox)
            layer_layout.addLayout(dw_layout)

            self.delta_mush_layout.addLayout(layer_layout)

    def update_layer_distance_weight(self, index, value):
        """
        Updates the 'distanceWeight' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            value (float): New distance weight value to apply.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["distanceWeight"] = value

    def update_layer_smoothing_iterations(self, index, value):
        """
        Updates the 'smoothingIterations' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            value (int): Number of smoothing iterations to set.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["smoothingIterations"] = value


class TabWidgetMasking(TabWidget):
    def __init__(self, parent=None, addon=None, definition=None, *args, **kwargs):
        """
        Initialize the AttrWidget.

        Args:
            parent (QWidget): The parent widget.
            addon (MeshMorpherAddon): The addon associated with this widget.
            definition (MeshMorpherDefinition): The definition associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, addon=addon, definition=definition, *args, **kwargs)
        # Add Button
        self.add_layer_button = ui_qt.QtWidgets.QPushButton()
        self.add_layer_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        self.add_layer_button.clicked.connect(self.add_layer)
        self.content_layout.addWidget(self.add_layer_button)
        # Mask RBF Layers
        self.masking_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.addLayout(self.masking_layout)
        self.refresh_layers()

    def refresh_layers(self):
        """
        Creates UI elements for each layer, including name fields and delete buttons.
        """
        # Clear layout before recreating UI (avoids duplicates)
        while self.masking_layout.count():
            item = self.masking_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layer_layout(item.layout())

        for index, layer in enumerate(self.addon.layers):
            layer_layout = ui_qt.QtWidgets.QVBoxLayout()

            # Layer Name
            name_and_delete_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Name:")
            layer_field = ui_qt.QtWidgets.QLineEdit(layer.get("name", ""))
            layer_field.textChanged.connect(partial(self.update_layer_name, index))
            name_and_delete_layout.addWidget(label)
            name_and_delete_layout.addWidget(layer_field)

            # Delete Button
            delete_button = ui_qt.QtWidgets.QPushButton()
            delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_button.clicked.connect(partial(self.delete_layer, index))
            name_and_delete_layout.addWidget(delete_button)
            layer_layout.addLayout(name_and_delete_layout)

            # Vertices
            vertices_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Vertices:")
            layer_field = ui_qt.QtWidgets.QLineEdit(layer.get("vertices", ""))
            layer_field.textChanged.connect(partial(self.update_layer_vertices, index))
            vertices_layout.addWidget(label)
            vertices_layout.addWidget(layer_field)

            # Get Button
            get_vertices_button = ui_qt.QtWidgets.QPushButton("GET")
            get_vertices_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            get_vertices_button.clicked.connect(partial(self.update_vertices_field_with_selection, index))
            select_vertices_button = ui_qt.QtWidgets.QPushButton("SELECT")
            select_vertices_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            select_vertices_button.clicked.connect(partial(self.select_layer_vertices, index))
            vertices_layout.addWidget(get_vertices_button)
            vertices_layout.addWidget(select_vertices_button)
            layer_layout.addLayout(vertices_layout)

            # Opacity
            dw_layout = ui_qt.QtWidgets.QHBoxLayout()
            dw_layout.setContentsMargins(0, 0, 0, 0)  # L-T-R-B
            label = ui_qt.QtWidgets.QLabel(f"Opacity:")
            dw_slider = ui_qt_utils.QDoubleSlider(ui_qt.QtLib.Orientation.Horizontal)
            spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
            spinbox.setDecimals(3)
            dw_slider.link_spin_box(spinbox)
            dw_slider.set_double_range(min_double=0, max_double=1)
            dw_slider.set_double_value(layer.get("opacity", 1.0))
            dw_slider.doubleValueChanged.connect(partial(self.update_layer_opacity, index))
            tooltip = "Opacity of the masked areas. Range is 0 to 1 (e.g. 0.5 = 50%)"
            dw_slider.setToolTip(tooltip)
            label.setToolTip(tooltip)
            spinbox.setToolTip(tooltip)
            dw_layout.addWidget(label)
            dw_layout.addWidget(dw_slider)
            dw_layout.addWidget(spinbox)
            layer_layout.addLayout(dw_layout)

            # Skip translations
            skip_translations_values = layer.get("skip_translations", [0, 0, 0])
            skip_layout = ui_qt.QtWidgets.QHBoxLayout()
            skip_layout.setContentsMargins(0, 0, 0, 0)  # L-T-R-B
            checkbox_tx = ui_qt.QtWidgets.QCheckBox("Skip TX")
            checkbox_tx.setChecked(skip_translations_values[0])
            checkbox_tx.setToolTip("Skip translation X")
            checkbox_tx.stateChanged.connect(partial(self.update_layer_skip_translations, index, 0))
            checkbox_ty = ui_qt.QtWidgets.QCheckBox("Skip TY")
            checkbox_ty.setChecked(skip_translations_values[1])
            checkbox_ty.setToolTip("Skip translation Y")
            checkbox_ty.stateChanged.connect(partial(self.update_layer_skip_translations, index, 1))
            checkbox_tz = ui_qt.QtWidgets.QCheckBox("Skip TZ")
            checkbox_tz.setChecked(skip_translations_values[2])
            checkbox_tz.setToolTip("Skip translation Z")
            checkbox_tz.stateChanged.connect(partial(self.update_layer_skip_translations, index, 2))
            skip_layout.addWidget(checkbox_tx)
            skip_layout.addWidget(checkbox_ty)
            skip_layout.addWidget(checkbox_tz)
            layer_layout.addLayout(skip_layout)

            self.masking_layout.addLayout(layer_layout)

    def update_layer_opacity(self, index, value):
        """
        Updates the 'opacity' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            value (float): New opacity value to set (typically between 0.0 and 1.0).
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["opacity"] = value

    def update_layer_skip_translations(self, index, axis, value):
        """
        Updates the 'skip translations' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            axis (int): 0, 1 or 2. X, Y or Z.
            value (int): state value from the checkbox widget.
        """
        skip_value_map = {0: 0, 2: 1}
        skip_values = [0, 0, 0]
        if "skip_translations" in self.addon.layers[index].keys():
            skip_values = self.addon.layers[index]["skip_translations"]
        skip_values[axis] = skip_value_map[value]
        self.addon.layers[index]["skip_translations"] = skip_values


class TabWidgetAnchor(TabWidget):
    def __init__(self, parent=None, addon=None, definition=None, *args, **kwargs):
        """
        Initialize the AttrWidget.

        Args:
            parent (QWidget): The parent widget.
            addon (MeshMorpherAddon): The addon associated with this widget.
            definition (MeshMorpherDefinition): The definition associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, addon=addon, definition=definition, *args, **kwargs)
        # Add Button
        self.add_layer_button = ui_qt.QtWidgets.QPushButton()
        self.add_layer_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        self.add_layer_button.clicked.connect(self.add_layer)
        self.content_layout.addWidget(self.add_layer_button)
        # Anchor Layers
        self.anchor_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.addLayout(self.anchor_layout)
        self.refresh_layers()

    def refresh_layers(self):
        """
        Creates UI elements for each layer, including name fields and delete buttons.
        """
        # Clear layout before recreating UI (avoids duplicates)
        while self.anchor_layout.count():
            item = self.anchor_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layer_layout(item.layout())

        for index, layer in enumerate(self.addon.layers):
            layer_layout = ui_qt.QtWidgets.QVBoxLayout()

            # Layer Name
            name_and_delete_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Name:")
            layer_field = ui_qt.QtWidgets.QLineEdit(layer.get("name", ""))
            layer_field.textChanged.connect(partial(self.update_layer_name, index))
            name_and_delete_layout.addWidget(label)
            name_and_delete_layout.addWidget(layer_field)

            # Delete Button
            delete_button = ui_qt.QtWidgets.QPushButton()
            delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_button.clicked.connect(partial(self.delete_layer, index))
            name_and_delete_layout.addWidget(delete_button)
            layer_layout.addLayout(name_and_delete_layout)

            # Anchor
            anchor_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Anchor point (vertex):")
            layer_field = ui_qt.QtWidgets.QLineEdit(str(layer.get("anchor", "")))
            layer_field.textChanged.connect(partial(self.update_layer_anchor, index))
            anchor_layout.addWidget(label)
            anchor_layout.addWidget(layer_field)
            get_anchor_button = ui_qt.QtWidgets.QPushButton("GET")
            get_anchor_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            get_anchor_button.clicked.connect(partial(self.update_anchor_field_with_selection, index))
            select_anchor_button = ui_qt.QtWidgets.QPushButton("SELECT")
            select_anchor_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            select_anchor_button.clicked.connect(partial(self.select_layer_anchor, index))
            anchor_layout.addWidget(get_anchor_button)
            anchor_layout.addWidget(select_anchor_button)
            layer_layout.addLayout(anchor_layout)

            # Vertices
            vertices_layout = ui_qt.QtWidgets.QHBoxLayout()
            label = ui_qt.QtWidgets.QLabel(f"Vertices:")
            layer_field = ui_qt.QtWidgets.QLineEdit(layer.get("vertices", ""))
            layer_field.textChanged.connect(partial(self.update_layer_vertices, index))
            vertices_layout.addWidget(label)
            vertices_layout.addWidget(layer_field)
            get_vertices_button = ui_qt.QtWidgets.QPushButton("GET")
            get_vertices_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            get_vertices_button.clicked.connect(partial(self.update_vertices_field_with_selection, index))
            select_vertices_button = ui_qt.QtWidgets.QPushButton("SELECT")
            select_vertices_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            select_vertices_button.clicked.connect(partial(self.select_layer_vertices, index))
            vertices_layout.addWidget(get_vertices_button)
            vertices_layout.addWidget(select_vertices_button)
            layer_layout.addLayout(vertices_layout)

            # Opacity
            dw_layout = ui_qt.QtWidgets.QHBoxLayout()
            dw_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            label = ui_qt.QtWidgets.QLabel(f"Opacity:")
            dw_slider = ui_qt_utils.QDoubleSlider(ui_qt.QtLib.Orientation.Horizontal)
            spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
            spinbox.setDecimals(3)
            dw_slider.link_spin_box(spinbox)
            dw_slider.set_double_range(min_double=0, max_double=1)
            dw_slider.set_double_value(layer.get("opacity", 1.0))
            dw_slider.doubleValueChanged.connect(partial(self.update_layer_opacity, index))
            tooltip = "Opacity of the masked areas. Range is 0 to 1 (e.g. 0.5 = 50%)"
            dw_slider.setToolTip(tooltip)
            label.setToolTip(tooltip)
            spinbox.setToolTip(tooltip)
            dw_layout.addWidget(label)
            dw_layout.addWidget(dw_slider)
            dw_layout.addWidget(spinbox)
            layer_layout.addLayout(dw_layout)

            self.anchor_layout.addLayout(layer_layout)

    def update_layer_opacity(self, index, value):
        """
        Updates the 'opacity' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            value (float): New opacity value to set (typically between 0.0 and 1.0).
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["opacity"] = value


class TabWidgetRenaming(TabWidget):
    def __init__(self, parent=None, addon=None, definition=None, *args, **kwargs):
        """
        Initialize the AttrWidget.

        Args:
            parent (QWidget): The parent widget.
            addon (MeshMorpherAddon): The addon associated with this widget.
            definition (MeshMorpherDefinition): The definition associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, addon=addon, definition=definition, *args, **kwargs)

        # Override
        override_tool_tip = "Overrides the entire name of the output mesh."
        override_layout = ui_qt.QtWidgets.QHBoxLayout()
        override_checkbox = ui_qt.QtWidgets.QCheckBox()
        override_label = ui_qt.QtWidgets.QLabel(f"Override:")
        override_text_field = ui_qt.QtWidgets.QLineEdit()
        override_text_field.setPlaceholderText("<override-name>")
        override_checkbox.toggled.connect(lambda checked, field=override_text_field: field.setEnabled(checked))
        override_checkbox.setChecked(addon.apply_override)  # Initial value
        override_text_field.setEnabled(addon.apply_override)  # Initial value
        override_text_field.setText(addon.override)  # Initial value
        override_checkbox.setToolTip(override_tool_tip)
        override_label.setToolTip(override_tool_tip)
        override_label.setToolTip(override_tool_tip)
        override_layout.addWidget(override_checkbox)
        override_layout.addWidget(override_label)
        override_layout.addWidget(override_text_field)
        self.content_layout.addLayout(override_layout)
        override_checkbox.toggled.connect(self.update_override_state)
        override_text_field.textChanged.connect(self.update_override)

        # Prefix, Suffix
        prefix_suffix_layout = ui_qt.QtWidgets.QHBoxLayout()
        prefix_tool_tip = "Adds a prefix to the output mesh."
        prefix_checkbox = ui_qt.QtWidgets.QCheckBox()
        prefix_label = ui_qt.QtWidgets.QLabel(f"Prefix:")
        prefix_text_field = ui_qt.QtWidgets.QLineEdit()
        prefix_text_field.setPlaceholderText("<prefix>")
        prefix_checkbox.toggled.connect(lambda checked, field=prefix_text_field: field.setEnabled(checked))
        prefix_checkbox.toggled.connect(self.update_prefix_state)
        prefix_text_field.textChanged.connect(self.update_prefix)
        prefix_checkbox.setChecked(addon.apply_prefix)  # Initial value
        prefix_text_field.setEnabled(addon.apply_prefix)  # Initial value
        prefix_text_field.setText(addon.prefix)  # Initial value
        prefix_checkbox.setToolTip(prefix_tool_tip)
        prefix_label.setToolTip(prefix_tool_tip)
        prefix_text_field.setToolTip(prefix_tool_tip)
        prefix_suffix_layout.addWidget(prefix_checkbox)
        prefix_suffix_layout.addWidget(prefix_label)
        prefix_suffix_layout.addWidget(prefix_text_field)

        suffix_checkbox = ui_qt.QtWidgets.QCheckBox()
        suffix_tool_tip = "Adds a suffix to the output mesh."
        suffix_label = ui_qt.QtWidgets.QLabel(f"Suffix:")
        suffix_text_field = ui_qt.QtWidgets.QLineEdit()
        suffix_text_field.setPlaceholderText("<suffix>")
        suffix_checkbox.toggled.connect(lambda checked, field=suffix_text_field: field.setEnabled(checked))
        suffix_checkbox.toggled.connect(self.update_suffix_state)
        suffix_text_field.textChanged.connect(self.update_suffix)
        suffix_checkbox.setChecked(addon.apply_suffix)  # Initial value
        suffix_text_field.setEnabled(addon.apply_suffix)  # Initial value
        suffix_text_field.setText(addon.suffix)  # Initial value
        suffix_checkbox.setToolTip(suffix_tool_tip)
        suffix_label.setToolTip(suffix_tool_tip)
        suffix_text_field.setToolTip(suffix_tool_tip)
        prefix_suffix_layout.addWidget(suffix_checkbox)
        prefix_suffix_layout.addWidget(suffix_label)
        prefix_suffix_layout.addWidget(suffix_text_field)

        self.content_layout.addLayout(prefix_suffix_layout)

        separator = ui_qt.QtWidgets.QFrame()
        separator.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        separator.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        self.content_layout.addWidget(separator)

        # Add Button
        self.add_layer_button = ui_qt.QtWidgets.QPushButton()
        self.add_layer_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        self.add_layer_button.clicked.connect(self.add_layer)
        self.content_layout.addWidget(self.add_layer_button)
        # Mask RBF Layers
        self.masking_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.addLayout(self.masking_layout)
        self.refresh_layers()

    def refresh_layers(self):
        """
        Creates UI elements for each layer, including name fields and delete buttons.
        """
        # Clear layout before recreating UI (avoids duplicates)
        while self.masking_layout.count():
            item = self.masking_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layer_layout(item.layout())

        for index, layer in enumerate(self.addon.layers):
            layer_layout = ui_qt.QtWidgets.QVBoxLayout()

            # Layer Search/Replace
            tool_tip = "Search/Replace fields. Available environment variables:\n"
            tool_tip += "$CACHE = The name of the cache file.\n"
            tool_tip += "$SUBJECT = The short name of the subject mesh."
            name_and_delete_layout = ui_qt.QtWidgets.QHBoxLayout()
            label_search = ui_qt.QtWidgets.QLabel(f"Search:")
            search_field = ui_qt.QtWidgets.QLineEdit(layer.get("search", ""))
            search_field.setPlaceholderText("<search-string>")
            search_field.textChanged.connect(partial(self.update_layer_search, index))
            replace_field = ui_qt.QtWidgets.QLineEdit(layer.get("replace", ""))
            replace_field.setPlaceholderText("<replace-string>")
            replace_field.textChanged.connect(partial(self.update_layer_replace, index))
            label_replace = ui_qt.QtWidgets.QLabel(f"Replace:")
            name_and_delete_layout.addWidget(label_search)
            name_and_delete_layout.addWidget(search_field)
            name_and_delete_layout.addWidget(label_replace)
            name_and_delete_layout.addWidget(replace_field)
            label_search.setToolTip(tool_tip)
            search_field.setToolTip(tool_tip)
            label_replace.setToolTip(tool_tip)
            replace_field.setToolTip(tool_tip)

            # Delete Button
            delete_button = ui_qt.QtWidgets.QPushButton()
            delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_button.clicked.connect(partial(self.delete_layer, index))
            name_and_delete_layout.addWidget(delete_button)
            layer_layout.addLayout(name_and_delete_layout)

            self.masking_layout.addLayout(layer_layout)

    def update_layer_search(self, index, value):
        """
        Updates the 'search' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            value (str): New search value to set.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["search"] = value

    def update_layer_replace(self, index, value):
        """
        Updates the 'replace' field of the layer dictionary at the given index.
        Args:
            index (int): Index of the layer to update.
            value (str): New replace value to set.
        """
        if 0 <= index < len(self.addon.layers):
            self.addon.layers[index]["replace"] = value

    def update_override_state(self, state):
        """
        Updates the 'apply_override' variable with a new state.
        Args:
            state (bool): New state to set for apply_override.
        """
        self.addon.apply_override = state

    def update_prefix_state(self, state):
        """
        Updates the 'apply_override' variable with a new state.
        Args:
            state (bool): New state to set for apply_prefix.
        """
        self.addon.apply_prefix = state

    def update_suffix_state(self, state):
        """
        Updates the 'apply_override' variable with a new state.
        Args:
            state (bool): New state to set for apply_suffix.
        """
        self.addon.apply_suffix = state

    def update_override(self, override):
        """
        Updates the 'override' variable with a new value.
        Args:
            override (str): New override value to apply.
        """
        self.addon.override = override

    def update_prefix(self, prefix):
        """
        Updates the 'prefix' variable with a new value.
        Args:
            prefix (str): New prefix value to apply.
        """
        self.addon.prefix = prefix

    def update_suffix(self, suffix):
        """
        Updates the 'suffix' variable with a new value.
        Args:
            suffix (str): New suffix value to apply.
        """
        self.addon.suffix = suffix


if __name__ == "__main__":
    import gt.tools.mesh_morpher.morpher_framework as tools_morpher_frm

    # Create Test Definition and Addon
    app = ui_qt.QtWidgets.QApplication(sys.argv)
    a_definition = tools_morpher_frm.MorpherDefinition()
    a_definition.set_subject_mesh("subject_mesh")
    a_delta_mush_addon = a_definition.get_addons("DeltaMush")[0]

    # Zippers Layer
    test_layers = [{"name": "zippers", "distanceWeight": 1, "smoothingIterations": 10, "vertices": "[0:370]"}]
    # Bottom Layer
    bottom_vertices = (
        "[371:373], [375:409], [411:812], [846:895], [1438:1440], [1548:1571], [1850], [1857], "
        "[1882:1890], [1963:1964], [1968:1979], [2009:2010], [2129:2182], [2235:2236], [2238:2241], "
        "[2247:2248], [2250:2253], [2259:2260], [2262:2263], [2352:2375], [2381:2382], [2384:2385], "
        "[2480:2503], [2510], [2517], [2541:2549], [2621:2622], [2624:2635], [2653:2705], [2742:2743], "
        "[2745:2748], [2754:2755], [2757:2760], [2766:2767], [2769:2770], [2786:2807], [2813:2814], "
        "[2816:2817], [2821:2830], [3263:3268], [3278:3308], [3446:3476], [3485:3758], [3787:3800], "
        "[3857], [3891:3903], [3913:3926], [3968:3969], [3971], [3981:3983], [4435:4436], [4464], "
        "[4520:4521]"
    )
    test_layers.append({"name": "bottom", "vertices": bottom_vertices})
    a_delta_mush_addon.set_layers(test_layers)

    # Create and show the AddonTab widget
    window = TabWidgetDeltaMush(addon=a_delta_mush_addon, definition=a_definition)
    window.setWindowTitle("Mesh Morpher Addon Widgets")
    window.resize(400, 300)
    window.show()

    # Execute the application
    sys.exit(app.exec_())
