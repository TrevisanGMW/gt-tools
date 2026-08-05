"""
Auto Rigger ngSkinTools2 Skin Weights Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *
import gt.utils.ngskin as utils_ng


class AttrWidgetModuleNGSkinWeights(AttrWidget):
    """Attribute editor for ModuleNGSkinWeights."""

    def __init__(self, parent=None, *args, **kwargs):
        """Initializes the ngSkinTools2 skin weights attribute widget.

        Args:
            parent (QWidget, optional): Parent widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="ngSkinTools2 Import")
        self.add_module_attr_widget_path(attr_name="weights_dir", dir_only=True)
        self.add_module_attr_widget_combobox(
            attr_name="vertex_transfer_mode",
            items=utils_ng.VertexTransferMode.get_values(),
            nice_name="Vertex Mapping",
            tooltip=(
                "Closest point transfers by surface proximity. UV space uses UVs. "
                "Vertex ID requires matching topology."
            ),
        )
        import_behavior_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.add_module_attr_widget_checkbox(
            attr_name="keep_existing_layers",
            layout=import_behavior_layout,
            tooltip=(
                "When enabled, layers already present on the target remain intact and imported layers are added "
                "above them. Disable this to clear the target's existing ngSkinTools2 layers before importing. "
                "This affects ngSkinTools2 layer data, not whether the Maya skinCluster is deleted."
            ),
        )
        self.add_module_attr_widget_checkbox(
            attr_name="delete_custom_nodes_after_import",
            layout=import_behavior_layout,
            tooltip=(
                "When enabled, ngSkinTools2 custom data and display nodes are removed from every successfully "
                "imported target after all files finish importing. The resulting weights remain in the standard "
                "Maya skinCluster, but editable ngSkinTools2 layers, masks, and layer history are permanently lost. "
                "Disable this when the scene must retain editable ngSkinTools2 layers."
            ),
        )
        self.content_layout.addLayout(import_behavior_layout)

        file_behavior_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.add_module_attr_widget_checkbox(
            attr_name="bind_missing_targets",
            layout=file_behavior_layout,
            tooltip=(
                "When enabled, an unbound target mesh receives a new Maya skinCluster before import. Influences "
                "are read from the ngSkinTools2 JSON file, passed through Influence Name Mapping, and must already "
                "exist in the scene. Disable this to require every target to be bound in advance; unbound targets "
                "will then be skipped without changing the scene."
            ),
        )
        self.clear_target_dir_chk = self.add_module_attr_widget_checkbox(
            attr_name="clear_target_dir",
            nice_name="Clear Target Directory When Writing",
            layout=file_behavior_layout,
            tooltip=(
                "When enabled, existing JSON weight files in the configured weights directory are deleted before "
                "Write Weights exports the current selection. Other file types are preserved. Disable this to keep "
                "existing exports and overwrite only files whose mesh names match the current selection."
            ),
        )
        self.content_layout.addLayout(file_behavior_layout)

        self.add_widget_separator_line(label_text="Influence Mapping")
        mapping_identity_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.add_module_attr_widget_checkbox(
            attr_name="use_name_matching",
            layout=mapping_identity_layout,
            tooltip=(
                "Matches exported influences to target skinCluster influences by name. ngSkinTools2 compares the "
                "available DAG names after any explicit Influence Name Mapping entries are applied. Explicit name "
                "mapping automatically enables name matching for that import, even if this option is disabled."
            ),
        )
        self.add_module_attr_widget_checkbox(
            attr_name="use_label_matching",
            layout=mapping_identity_layout,
            tooltip=(
                "Matches influences using Maya joint labels: the joint side value and label text. This is useful "
                "when source and target joint names differ but both skeletons have consistent Maya joint labels. "
                "Unlabeled or inconsistently labeled joints will not receive a match from this rule."
            ),
        )
        self.content_layout.addLayout(mapping_identity_layout)

        mapping_fallback_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.add_module_attr_widget_checkbox(
            attr_name="use_distance_matching",
            layout=mapping_fallback_layout,
            tooltip=(
                "Matches influences by comparing their world-space pivot positions. Candidate joints farther apart "
                "than Distance Threshold are rejected. This can map renamed but spatially identical skeletons; use "
                "a small threshold to prevent nearby joints such as fingers or facial joints from being confused."
            ),
        )
        self.add_module_attr_widget_checkbox(
            attr_name="use_dg_link_matching",
            layout=mapping_fallback_layout,
            tooltip=(
                "Allows ngSkinTools2 to match influences through dependency-graph links, using its configured "
                "opposite-influence relationship attribute. This is mainly useful in pipelines that explicitly "
                "connect paired or corresponding joints. It has no effect when those DG links are not present."
            ),
        )
        self.content_layout.addLayout(mapping_fallback_layout)
        self.add_module_attr_widget_double_spinbox(
            attr_name="influence_distance_threshold",
            nice_name="Distance Threshold",
            min_double=0.0,
            max_double=1000.0,
            precision=6,
        )
        self.add_module_attr_widget_dictionary_editor(
            attr_name="influence_name_mapping",
            nice_name="Influence Name Mapping",
            tooltip="Open the source-influence to destination-influence mapping dictionary.",
            dict_editor_tooltip=(
                "Enter a Python dictionary where each key is an influence name stored in the exported ngSkinTools2 "
                "file and each value is the influence that should receive those weights in the current scene. Keys "
                "may be full DAG paths or short names; namespace-free short-name lookup is supported. Values must "
                "identify influences that exist on, or can be bound to, the target. Only renamed influences need "
                "entries.\n\n"
                "Example:\n"
                "{\n"
                "    \"oldRig:hip_jnt\": \"C_hip_jnt\",\n"
                "    \"oldRig:knee_L_jnt\": \"L_knee_jnt\",\n"
                "    \"|oldRig|ankle_R_jnt\": \"|character|skeleton|R_ankle_jnt\"\n"
                "}"
            ),
        )
        self.add_module_attr_widget_dictionary_editor(
            attr_name="target_name_mapping",
            nice_name="Target Name Mapping",
            tooltip="Open the exported-file name to destination-mesh mapping dictionary.",
            dict_editor_tooltip=(
                "Enter a Python dictionary where each key is an exported weight file name without the .json "
                "extension and each value is the destination mesh in the current Maya scene. Files without an "
                "entry use their own base name as the target, so only renamed meshes need to be listed. This mapping "
                "changes which mesh receives a file; it does not rename any scene nodes.\n\n"
                "For example, body_geo.json and head_geo.json can target renamed render meshes with:\n"
                "{\n"
                "    \"body_geo\": \"render_body_geo\",\n"
                "    \"head_geo\": \"character:render_head_geo\"\n"
                "}"
            ),
        )

        self.add_widget_separator_line(label_text="Utilities")
        layout = ui_qt.QtWidgets.QHBoxLayout()
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Weights Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_weights_dir)
        write_weights_btn = ui_qt.QtWidgets.QPushButton("Write Weights")
        write_weights_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_weights_btn.clicked.connect(self.write_weights)
        layout.addWidget(open_dir_btn)
        layout.addWidget(write_weights_btn)
        self.scroll_content_layout.addLayout(layout)

    def open_weights_dir(self):
        """Creates and opens the configured weights directory."""
        parsed_path = self.module.parse_path(path=self.module.weights_dir)
        parsed_path = core_io.make_directory(parsed_path)
        if not parsed_path or not os.path.isdir(parsed_path):
            logger.warning(f'Unable to open missing path: "{parsed_path}".')
            return
        utils_system.open_file_dir(parsed_path)

    def write_weights(self):
        """Writes ngSkinTools2 data for the current Maya selection."""
        self.module.write_weights_from_selection(clear_target_dir=self.clear_target_dir_chk.isChecked())
