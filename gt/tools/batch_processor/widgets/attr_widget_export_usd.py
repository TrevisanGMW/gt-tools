"""
Batch Processor USD Export Task Attribute Widget
"""

from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetUsdExportTask(AttrWidgetTask):
    """Attribute widget for the USD export task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the USD export task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (UsdExportTask, optional): USD export task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings(
            scene_io_settings={
                "load_mode_key": "source_load_mode",
                "output_extension_key": "output_extension",
                "output_extension_value": self.get_visible_usd_extension(),
                "output_extension_values": [".usd", ".usda", ".usdc"],
                "output_extension_setter": self.set_usd_output_extension,
            }
        )
        self.frame_start_spin = None
        self.frame_end_spin = None
        self.add_widget_separator_line(label_text="USD Export Preferences")

        frame_options_layout = ui_qt.QtWidgets.QHBoxLayout()
        frame_options_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Animation", "animation", "Export a frame range instead of a single sample."),
            ("Static Export", "static_export", "Export a static single-sample USD file."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=frame_options_layout,
                tooltip=tooltip,
            )
        frame_options_layout.addStretch()
        self.content_layout.addLayout(frame_options_layout)

        frame_range_layout = self.add_labeled_layout(
            "Frame Range",
            tooltip="Manual frame range used when Auto Frame Range is disabled.",
        )
        auto_frame_checkbox = self.add_checkbox(
            "Auto",
            self.task.settings.get("auto_frame_range"),
            self.set_auto_frame_range,
            layout=frame_range_layout,
            tooltip="Use the current scene playback range.",
        )
        auto_frame_checkbox.setToolTip("Use the current scene playback range.")
        frame_start_label = ui_qt.QtWidgets.QLabel("Start:")
        attr_widget_base.configure_label_for_scaled_displays(frame_start_label)
        frame_start_label.setToolTip("Start frame used when Auto Frame Range is disabled.")
        frame_range_layout.addWidget(frame_start_label)
        self.frame_start_spin = self.create_frame_spin_box(
            self.task.settings.get("frame_start"),
            partial(self.set_task_setting, key="frame_start"),
            tooltip="Start frame used when Auto Frame Range is disabled.",
        )
        frame_range_layout.addWidget(self.frame_start_spin)
        frame_end_label = ui_qt.QtWidgets.QLabel("End:")
        attr_widget_base.configure_label_for_scaled_displays(frame_end_label)
        frame_end_label.setToolTip("End frame used when Auto Frame Range is disabled.")
        frame_range_layout.addWidget(frame_end_label)
        self.frame_end_spin = self.create_frame_spin_box(
            self.task.settings.get("frame_end"),
            partial(self.set_task_setting, key="frame_end"),
            tooltip="End frame used when Auto Frame Range is disabled.",
        )
        frame_range_layout.addWidget(self.frame_end_spin)
        frame_range_layout.addStretch()
        self.refresh_frame_range_enabled_state()

        roots_layout = ui_qt.QtWidgets.QHBoxLayout()
        roots_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Auto Roots", "auto_detect_roots", "Find export roots like the Maya-to-USD batch script."),
            ("Joints", "include_joints", "Include top-level joint roots and joint parent groups."),
            ("Locators", "include_locators", "Include locator transforms as export roots."),
            ("Curves", "include_curves", "Include curve transforms as export roots."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=roots_layout,
                tooltip=tooltip,
            )
        roots_layout.addStretch()
        self.content_layout.addLayout(roots_layout)

        self.add_text_field(
            "Target Node",
            self.task.settings.get("target_node"),
            partial(self.set_task_setting, key="target_node"),
            placeholder="Optional preferred export root node. Leave empty to skip.",
            tooltip="Optional preferred root node added when found. Leave empty to skip this lookup.",
        )
        self.add_text_area(
            "Target Roots",
            "\n".join(self.task.settings.get("target_roots") or []),
            partial(self.set_task_setting_list_from_text, key="target_roots"),
            placeholder="One explicit root node per line. Leave empty to use automatic roots.",
            tooltip="Explicit root nodes to include in the USD export.",
        )

        scene_layout = ui_qt.QtWidgets.QHBoxLayout()
        scene_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Force Z Up", "force_z_up", "Temporarily export with Z-up orientation."),
            ("Zero Root Rotation", "zero_root_rotation", "Temporarily zero root rotations before export."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=scene_layout,
                tooltip=tooltip,
            )
        scene_layout.addStretch()
        self.content_layout.addLayout(scene_layout)

        content_layout = ui_qt.QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Materials", "materials", "Export USD material data."),
            ("Skeletons", "skeletons", "Export skeleton data."),
            ("Skin", "skin", "Export skin data."),
            ("Blend Shapes", "blend_shapes", "Export blend shape data."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=content_layout,
                tooltip=tooltip,
            )
        content_layout.addStretch()
        self.content_layout.addLayout(content_layout)

        content_layout_two = ui_qt.QtWidgets.QHBoxLayout()
        content_layout_two.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Color Sets", "color_sets", "Export color sets."),
            ("UVs", "uvs", "Export UV sets."),
            ("Visibility", "visibility", "Export visibility data."),
            ("Strip Namespaces", "strip_namespaces", "Strip Maya namespaces during export."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=content_layout_two,
                tooltip=tooltip,
            )
        content_layout_two.addStretch()
        self.content_layout.addLayout(content_layout_two)

        advanced_layout = ui_qt.QtWidgets.QHBoxLayout()
        advanced_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Merge Xform/Shape", "merge_transform_and_shape", "Merge transform and shape prims when supported."),
            ("Write Defaults", "write_defaults", "Write default-valued attributes to USD."),
            ("Suppress Warnings", "ignore_warnings", "Suppress Maya USD export warnings during automated runs."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=advanced_layout,
                tooltip=tooltip,
            )
        advanced_layout.addStretch()
        self.content_layout.addLayout(advanced_layout)

        self.add_text_area(
            "Native Custom Attributes",
            "\n".join(self.task.settings.get("native_custom_attributes") or []),
            partial(self.set_task_setting_list_from_text, key="native_custom_attributes"),
            placeholder="One Maya attribute per line, e.g. contact_heel_end_l.contactWeight.\n"
            "These are tagged for native MayaUSD attribute export.",
            tooltip="Attributes tagged through MayaUSD's USD_UserExportedAttributesJson mechanism.",
        )
        self.add_text_area(
            "Post Custom Data",
            "\n".join(self.task.settings.get("custom_data_attributes") or []),
            partial(self.set_task_setting_list_from_text, key="custom_data_attributes"),
            placeholder="One Maya attribute per line, e.g. SK_Universal_Simplified.collections.\n"
            "Values are injected into matching USD prim custom data after export.",
            tooltip="Attributes injected as USD prim custom data after export.",
        )
        self.content_layout.addStretch()

    def get_visible_usd_format(self):
        """Gets the visible USD format value.

        Returns:
            str: USD, USDA, or USDC.
        """
        usd_format = str(self.task.settings.get("usd_format") or "").strip(".").upper()
        extension = str(self.task.settings.get("output_extension") or ".usd").strip(".").upper()
        if extension in ["USDA", "USDC"] and usd_format == "USD":
            return extension
        if usd_format in ["USD", "USDA", "USDC"]:
            return usd_format
        if extension in ["USD", "USDA", "USDC"]:
            return extension
        return "USD"

    def get_visible_usd_extension(self):
        """Gets the visible USD output extension.

        Returns:
            str: USD extension with a leading dot.
        """
        return "." + self.get_visible_usd_format().lower()

    def set_usd_format(self, value):
        """Sets USD format and output extension from one UI value.

        Args:
            value (str): Visible USD format value.
        """
        value = str(value or "USD").upper()
        if value not in ["USD", "USDA", "USDC"]:
            value = "USD"
        self.task.settings["usd_format"] = value
        self.task.settings["output_extension"] = "." + value.lower()

    def set_usd_output_extension(self, value):
        """Sets USD format from an output extension value.

        Args:
            value (str): USD output extension value.
        """
        extension = str(value or ".usd").lower()
        if not extension.startswith("."):
            extension = "." + extension
        if extension not in [".usd", ".usda", ".usdc"]:
            extension = ".usd"
        self.task.settings["output_extension"] = extension
        self.task.settings["usd_format"] = extension.strip(".").upper()

    def set_auto_frame_range(self, value):
        """Sets automatic frame range and updates manual controls.

        Args:
            value (bool): Whether automatic frame range is enabled.
        """
        self.task.settings["auto_frame_range"] = bool(value)
        self.refresh_frame_range_enabled_state()

    def refresh_frame_range_enabled_state(self):
        """Updates manual frame widgets based on automatic frame range."""
        is_manual = not bool(self.task.settings.get("auto_frame_range", True))
        for widget in [self.frame_start_spin, self.frame_end_spin]:
            if widget:
                widget.setEnabled(is_manual)

    @staticmethod
    def create_frame_spin_box(value, setter, tooltip=None):
        """Creates a frame number spin box.

        Args:
            value (object): Current frame value.
            setter (callable): Setter called when the value changes.
            tooltip (str, optional): Tooltip text.

        Returns:
            QSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(-1000000, 1000000)
        try:
            spin_box.setValue(int(float(value)))
        except (TypeError, ValueError):
            spin_box.setValue(0)
        spin_box.setMinimumHeight(35)
        spin_box.setMinimumWidth(80)
        spin_box.setToolTip(tooltip or "Frame number.")
        spin_box.valueChanged.connect(lambda value_int: setter(value_int))
        return spin_box
