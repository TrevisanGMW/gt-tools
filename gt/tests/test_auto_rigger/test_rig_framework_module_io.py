"""Tests for Auto Rigger mirror persistence, module tree export and project import."""

import unittest
import sys
import os

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
from gt.tools.auto_rigger.rig_modules import RigModules
from gt.tests import maya_test_tools


class TestRigFrameworkModuleIO(unittest.TestCase):
    """Tests module serialization helpers used by the project widget and controller."""

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def setUp(self):
        maya_test_tools.force_new_scene()

    def create_group_project(self):
        """Creates a project with a group, a child, a grandchild and an unrelated module.

        Returns:
            tuple: The project, group, child, grandchild and unrelated modules.
        """
        project = tools_rig_frm.RigProject()
        group = RigModules.Utils.ModuleGroup()
        child = tools_rig_frm.ModuleGeneric(name="child")
        child.add_new_proxy()
        child.set_parent_uuid(group.get_proxies_uuids()[0])
        grandchild = tools_rig_frm.ModuleGeneric(name="grandchild")
        grandchild.add_new_proxy()
        grandchild.set_parent_uuid(child.get_proxies_uuids()[0])
        unrelated = tools_rig_frm.ModuleGeneric(name="unrelated")
        unrelated.add_new_proxy()
        for module in [group, child, unrelated, grandchild]:
            project.add_to_modules(module)
        return project, group, child, grandchild, unrelated

    def test_mirror_uuid_round_trip(self):
        """Restores the stored mirror source when reading a module dictionary."""
        source = tools_rig_frm.ModuleGeneric(name="source")
        target = tools_rig_frm.ModuleGeneric(name="target")
        target.set_mirror_uuid(source.get_uuid())

        loaded = tools_rig_frm.ModuleGeneric().read_data_from_dict(target.get_module_as_dict())

        expected = source.get_uuid()
        self.assertEqual(expected, loaded.get_mirror_uuid())

    def test_clear_mirror_uuid(self):
        """Removes the mirror source so it is no longer serialized."""
        target = tools_rig_frm.ModuleGeneric(name="target")
        target.set_mirror_uuid(tools_rig_frm.ModuleGeneric().get_uuid())

        target.clear_mirror_uuid()

        self.assertIsNone(target.get_mirror_uuid())
        self.assertNotIn("mirror", target.get_module_as_dict())

    def test_get_module_descendants(self):
        """Finds direct and indirect children in project order."""
        project, group, child, grandchild, unrelated = self.create_group_project()

        result = project.get_module_descendants(group)

        expected = [child, grandchild]
        self.assertEqual(expected, result)

    def test_get_module_tree_as_dict_includes_children(self):
        """Stores descendant modules under the children key."""
        project, group, child, grandchild, unrelated = self.create_group_project()

        result = project.get_module_tree_as_dict(group)

        children_key = tools_rig_const.RiggerConstants.MODULE_TREE_CHILDREN_KEY
        expected = [child.get_uuid(), grandchild.get_uuid()]
        self.assertEqual(expected, [child_dict.get("uuid") for child_dict in result.get(children_key)])
        self.assertEqual(group.get_uuid(), result.get("uuid"))

    def test_add_module_from_dict_imports_tree_with_new_uuids(self):
        """Imports a group tree with new UUIDs while keeping its hierarchy."""
        project, group, child, grandchild, unrelated = self.create_group_project()
        tree_dict = project.get_module_tree_as_dict(group)
        new_project = tools_rig_frm.RigProject()
        new_project.add_modules_from_dict_list([group.get_module_as_dict()], reinitialize_uuids=False)

        imported_group = new_project.add_module_from_dict(tree_dict)

        self.assertEqual(4, len(new_project.get_modules()))
        self.assertNotEqual(group.get_uuid(), imported_group.get_uuid())
        imported_descendants = new_project.get_module_descendants(imported_group)
        self.assertEqual(["child", "grandchild"], [module.get_name() for module in imported_descendants])
        imported_uuids = {imported_group.get_uuid()} | {module.get_uuid() for module in imported_descendants}
        original_uuids = {group.get_uuid(), child.get_uuid(), grandchild.get_uuid()}
        self.assertFalse(imported_uuids & original_uuids)

    def test_import_modules_from_project_dict_randomizes_uuids(self):
        """Appends modules, randomizing UUIDs and remapping mirror sources."""
        source_project, group, child, grandchild, unrelated = self.create_group_project()
        unrelated.set_mirror_uuid(child.get_uuid())
        project_dict = source_project.get_project_as_dict()
        target_project = tools_rig_frm.RigProject().read_data_from_dict(project_dict)

        imported_modules = target_project.import_modules_from_project_dict(project_dict, reinitialize_uuids=True)

        self.assertEqual(8, len(target_project.get_modules()))
        imported_dicts = [module.get_module_as_dict() for module in imported_modules]
        self.assertEqual([], source_project.get_uuid_conflicts(imported_dicts))
        imported_by_name = {module.get_name(): module for module in imported_modules}
        expected = imported_by_name.get("child").get_uuid()
        self.assertEqual(expected, imported_by_name.get("unrelated").get_mirror_uuid())

    def test_import_modules_from_project_dict_can_preserve_uuids(self):
        """Keeps UUIDs when randomization is disabled and reports the conflicts."""
        source_project, group, child, grandchild, unrelated = self.create_group_project()
        project_dict = source_project.get_project_as_dict()

        conflicts = source_project.get_uuid_conflicts(project_dict.get("modules"))
        imported_modules = tools_rig_frm.RigProject().import_modules_from_project_dict(
            project_dict, reinitialize_uuids=False
        )

        self.assertIn(group.get_uuid(), conflicts)
        expected = [module.get_uuid() for module in source_project.get_modules()]
        self.assertEqual(expected, [module.get_uuid() for module in imported_modules])


if __name__ == "__main__":
    unittest.main()
