"""
Auto Rigger Template for Generic Root
"""

import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.core.logger as core_log
import gt.core.uuid as core_uuid
import maya.cmds as cmds
import logging

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


def create_template_generic_root():
    """
    Creates a template project for a generic root, the most basic set of modules to start an asset rig.
    Returns:
        RigProject: A rig project containing modules used in a generic root
    """

    # Project Generic Root dictionary
    generic_root_dict = {
        "uuid": core_uuid.generate_uuid(short=True, short_length=6),  # Randomize UUID,
        "name": "GenericRoot",
        "modules": [
            {
                "module": "ModuleNewScene",
                "name": "New Scene",
                "uuid": "zje7f9gfmags",
                "active": True,
                "code": {"order": "pre_proxy"},
                "scene_options": {
                    "linear_unit": "centimeter",
                    "angular_unit": "degree",
                    "frame_rate": "30fps",
                    "multi_sample": True,
                    "multi_sample_count": 8,
                    "persp_clip_plane_near": 1,
                    "persp_clip_plane_far": 10000.0,
                    "display_textures": True,
                    "playback_frame_start": 1,
                    "playback_frame_end": 120,
                    "animation_frame_start": 1,
                    "animation_frame_end": 200,
                    "current_time": 1,
                },
                "proxies": {},
            },
            {
                "module": "ModuleRoot",
                "name": "Root",
                "uuid": "fho5n0v7tsur",
                "active": True,
                "prefix": "C",
                "orientation": {
                    "method": "inherit",
                    "aim_axis": [1, 0, 0],
                    "up_axis": [0, 1, 0],
                    "up_dir": [0, 1, 0],
                    "world_aligned": False,
                },
                "matches_proxy_rot": False,
                "proxies": {
                    "737b4d76d7b04c7a9b2320d56f28a37e": {
                        "name": "root",
                        "parent": None,
                        "transform": {
                            "position": [0.0, 0.0, 0.0],
                            "rotation": [0.0, 0.0, 0.0],
                            "scale": [1.0, 1.0, 1.0],
                        },
                        "attributes": {
                            "baseName": "root",
                            "prefix": "C",
                            "suffix": "",
                            "rotationOrder": 0,
                            "locatorScale": 3.0,
                            "driverUUID": "fho5n0v7tsur-proxy-root",
                            "autoColor": False,
                            "colorDefault": [0.6, 0.2, 1.0],
                            "colorRight": [0.2, 0.6, 1.0],
                            "colorLeft": [1.0, 0.4, 0.4],
                        },
                        "metadata": {"proxyPurpose": "root", "proxyDrivers": ["block", "fk"]},
                    }
                },
            },
            {
                "module": "ModuleAttributeHub",
                "name": "Visibility Control",
                "uuid": "tjxgeo6eudzt",
                "active": True,
                "code": {"order": "post_build"},
                "attr_switcher_shape": "_letter_v_pos_z",
                "attr_mapping": {"controlVisibility": None, "rootCtrl": ["C_root_offset.v"]},
                "attr_values": {"rootCtrl": 0},
                "parent_constraint_type": "point",
                "proxies": {
                    "7f4f175480e44ff393efc76b5b3f30be": {
                        "name": "visibility",
                        "parent": None,
                        "transform": {
                            "position": [0.0, 43.46640791537903, 0.0],
                            "rotation": [0.0, 0.0, 0.0],
                            "scale": [1.0, 1.0, 1.0],
                        },
                        "attributes": {
                            "baseName": "visibility",
                            "prefix": "",
                            "suffix": "",
                            "rotationOrder": 0,
                            "locatorScale": 1.0,
                            "driverUUID": "tjxgeo6eudzt-proxy-attributeHub",
                            "autoColor": False,
                            "colorDefault": [0.0, 1.0, 0.0],
                            "colorRight": [0.2, 0.6, 1.0],
                            "colorLeft": [1.0, 0.4, 0.4],
                        },
                        "metadata": {"proxyPurpose": "attributeHub"},
                    }
                },
            },
            {
                "module": "ModuleImportFile",
                "name": "Import File (Model)",
                "uuid": "kn2zimt4er6v",
                "active": True,
                "code": {"order": "post_skeleton"},
                "file_path": "{tests-data-dir}\\auto_rigger_resources\\geo\\cube.ma",
                "namespace": "",
                "merge_namespaces_on_clash": False,
                "reference": False,
                "transforms_parent": "geometry",
                "purge_display_layers": True,
                "deactivate_drawing_overrides": True,
                "proxies": {},
            },
            {
                "module": "ModuleSkinWeights",
                "name": "Skin Weights",
                "uuid": "121uq874ge9h",
                "active": False,
                "code": {"order": "post_skeleton"},
                "influences_dir": "{project-dir}\\influences",
                "weights_dir": "{project-dir}\\weights",
                "remove_unused_influences": True,
                "clear_target_dir": False,
                "proxies": {},
            },
            {
                "module": "ModuleSaveScene",
                "name": "Save Scene",
                "uuid": "4c51jmxanw4f",
                "active": False,
                "code": {"order": "post_build"},
                "file_path": "{project-dir}\\GenericRoot_rig.ma",
                "file_extension": ".ma",
                "proxies": {},
            },
            {
                "module": "ModuleExportSkeletalMesh",
                "name": "Export SKM",
                "uuid": "u3sd5o878qwd",
                "active": False,
                "code": {"order": "post_build"},
                "export_dir": "{project-dir}\\exports",
                "export_filename": "SKM_GenericRoot",
                "export_pose": "apose",
                "mesh_filter_include": "",
                "mesh_filter_exclude": "",
                "mesh_filter_short_names": False,
                "proxies": {},
            },
        ],
        "preferences": {
            "build_control_rig": True,
            "delete_proxy_after_build": True,
            "apply_control_rig_pose": False,
            "hide_skeleton": True,
            "view_fit_skeleton": True,
            "control_rig_pose_name": "tpose",
            "project_dir": "",
        },
    }
    generic_root_project = tools_rig_frm.RigProject()
    generic_root_project.read_data_from_dict(generic_root_dict)

    return generic_root_project


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    a_root_project = create_template_generic_root()
    a_root_project.build_proxy()
    a_root_project.build_rig()
    cmds.viewFit(all=True)
