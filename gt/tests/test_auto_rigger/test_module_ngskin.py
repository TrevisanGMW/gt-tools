"""Tests for the Auto Rigger ngSkinTools2 weights module."""

import os
import sys
import unittest

repository_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if repository_root not in sys.path:
    sys.path.append(repository_root)

import gt.tools.auto_rigger.modules.module_ngskin as module_ngskin
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.ui.resource_library as ui_res_lib
import gt.utils.ngskin as utils_ng


class TestModuleNGSkinWeights(unittest.TestCase):
    """Tests import-safe module state and serialization behavior."""

    def test_module_inheritance(self):
        """Tests that the module follows the Auto Rigger module framework."""
        module = module_ngskin.ModuleNGSkinWeights()
        self.assertIsInstance(module, tools_rig_frm.ModuleGeneric)

    def test_default_transfer_mode_is_closest_point(self):
        """Tests proximity transfer as the requested default behavior."""
        module = module_ngskin.ModuleNGSkinWeights()
        self.assertEqual(utils_ng.VertexTransferMode.CLOSEST_POINT, module.vertex_transfer_mode)

    def test_module_uses_ngskin_icon(self):
        """Tests that the ngSkinTools module has a distinct registered icon."""
        module = module_ngskin.ModuleNGSkinWeights()
        self.assertEqual(ui_res_lib.Icon.rigger_module_ngskin_weights, module.icon)

    def test_mapping_data_is_serialized(self):
        """Tests persistence for custom target and influence mappings."""
        module = module_ngskin.ModuleNGSkinWeights()
        module.influence_name_mapping = {"old_jnt": "new_jnt"}
        module.target_name_mapping = {"old_geo": "new_geo"}
        data = module.get_module_as_dict()
        self.assertEqual({"old_jnt": "new_jnt"}, data.get("influence_name_mapping"))
        self.assertEqual({"old_geo": "new_geo"}, data.get("target_name_mapping"))


if __name__ == "__main__":
    unittest.main()
