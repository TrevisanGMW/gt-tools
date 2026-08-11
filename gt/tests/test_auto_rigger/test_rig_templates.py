import os
import tempfile
import unittest

import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_templates as tools_rig_templates
from gt.tests import maya_test_tools


class TestRigTemplates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)

    def test_get_project_template_data_resets_project_directory(self):
        project = tools_rig_frm.RigProject(name="Template Test")
        project.set_project_dir_path("C:/project_resources")

        template_data = tools_rig_templates.get_project_template_data(project)

        expected_template_path = ""
        result_template_path = template_data["preferences"]["project_dir"]
        self.assertEqual(expected_template_path, result_template_path)

        expected_project_path = "C:/project_resources"
        result_project_path = project.get_project_dir_path()
        self.assertEqual(expected_project_path, result_project_path)

    def test_project_directory_has_resources_ignores_project_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_file_path = os.path.join(temp_dir, "character.rig")
            with open(project_file_path, "w", encoding="utf-8"):
                pass

            project = tools_rig_frm.RigProject()
            project.project_file_path = project_file_path
            project.set_project_dir_path(temp_dir)

            expected_without_resources = False
            result_without_resources = tools_rig_templates.project_directory_has_resources(project)
            self.assertEqual(expected_without_resources, result_without_resources)

            resource_file_path = os.path.join(temp_dir, "geometry.ma")
            with open(resource_file_path, "w", encoding="utf-8"):
                pass

            expected_with_resources = True
            result_with_resources = tools_rig_templates.project_directory_has_resources(project)
            self.assertEqual(expected_with_resources, result_with_resources)

            relative_resource_dir = os.path.join(temp_dir, "resources")
            os.makedirs(relative_resource_dir)
            relative_resource_path = os.path.join(relative_resource_dir, "character.ma")
            with open(relative_resource_path, "w", encoding="utf-8"):
                pass
            project.set_project_dir_path("resources")

            expected_relative_source_dir = os.path.normpath(relative_resource_dir)
            result_relative_source_dir = tools_rig_templates.get_project_resource_source_dir(project)
            self.assertEqual(expected_relative_source_dir, result_relative_source_dir)

    def test_copy_project_resources_excludes_project_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = os.path.join(temp_dir, "source")
            target_dir = os.path.join(temp_dir, "template_resources")
            os.makedirs(os.path.join(source_dir, "geo"))

            project_file_path = os.path.join(source_dir, "character.rig")
            root_resource_path = os.path.join(source_dir, "textures.txt")
            nested_resource_path = os.path.join(source_dir, "geo", "character.ma")
            for file_path in [project_file_path, root_resource_path, nested_resource_path]:
                with open(file_path, "w", encoding="utf-8"):
                    pass

            project = tools_rig_frm.RigProject()
            project.project_file_path = project_file_path
            project.set_project_dir_path(source_dir)

            copy_results = tools_rig_templates.copy_project_resources(project, target_dir)

            expected_copied_count = 2
            result_copied_count = copy_results["copied"]
            self.assertEqual(expected_copied_count, result_copied_count)

            expected_project_file_exists = False
            result_project_file_exists = os.path.exists(os.path.join(target_dir, "character.rig"))
            self.assertEqual(expected_project_file_exists, result_project_file_exists)

            expected_nested_resource_exists = True
            result_nested_resource_exists = os.path.exists(os.path.join(target_dir, "geo", "character.ma"))
            self.assertEqual(expected_nested_resource_exists, result_nested_resource_exists)


if __name__ == "__main__":
    unittest.main()
