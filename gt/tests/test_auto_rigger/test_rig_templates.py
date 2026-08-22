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

    def test_package_template_directories_and_resources(self):
        package_templates_dir = tools_rig_templates.get_package_template_source_dir()
        package_resources_dir = tools_rig_templates.get_package_template_resources_dir()

        expected_template_exists = True
        result_template_exists = os.path.isfile(os.path.join(package_templates_dir, "Biped_Base.rig"))
        self.assertEqual(expected_template_exists, result_template_exists)

        expected_resource_path = os.path.join(package_resources_dir, "Biped_Base")
        result_resource_path = tools_rig_templates.get_template_resource_path(
            "biped_base", package_resources_dir
        )
        self.assertEqual(expected_resource_path, result_resource_path)

    def test_rig_templates_keeps_package_templates_separate(self):
        original_user_templates = tools_rig_templates.TEMPLATE_SOURCE_DIR
        original_package_templates = tools_rig_templates.PACKAGE_TEMPLATE_SOURCE_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            user_templates_dir = os.path.join(temp_dir, "user_templates")
            package_templates_dir = os.path.join(temp_dir, "package_templates")
            os.makedirs(user_templates_dir)
            os.makedirs(package_templates_dir)
            with open(os.path.join(user_templates_dir, "user_template.rig"), "w", encoding="utf-8"):
                pass
            with open(os.path.join(package_templates_dir, "package_template.rig"), "w", encoding="utf-8"):
                pass

            tools_rig_templates.TEMPLATE_SOURCE_DIR = user_templates_dir
            tools_rig_templates.PACKAGE_TEMPLATE_SOURCE_DIR = package_templates_dir
            try:
                rig_templates = tools_rig_templates.RigTemplates(include_package_templates=True)
            finally:
                tools_rig_templates.TEMPLATE_SOURCE_DIR = original_user_templates
                tools_rig_templates.PACKAGE_TEMPLATE_SOURCE_DIR = original_package_templates

        expected_user_template = True
        result_user_template = "user_template" in rig_templates.get_dict_templates(include_py_templates=False)
        self.assertEqual(expected_user_template, result_user_template)

        expected_package_template = True
        result_package_template = "package_template" in rig_templates.get_dict_templates(
            include_py_templates=False,
            include_file_templates=False,
            include_package_templates=True,
        )
        self.assertEqual(expected_package_template, result_package_template)


if __name__ == "__main__":
    unittest.main()
