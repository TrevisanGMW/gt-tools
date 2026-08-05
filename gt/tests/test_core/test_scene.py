import os
import sys
import logging
import tempfile
import unittest
from unittest.mock import call, patch

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tests import maya_test_tools
from gt.core import feedback as core_feedback
from gt.core import scene as core_scene

cmds = maya_test_tools.cmds


def import_test_scene():
    """
    Open files from inside the test_*/data folder/cube_namespaces.mb
    Scene contains a cube named: "parentNS:childNS:grandchildNS:pCube1"
    """
    maya_test_tools.import_data_file("cube_namespaces.ma")


class TestSceneCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_frame_rate(self):
        import_test_scene()
        expected = 24
        result = core_scene.get_frame_rate()
        self.assertEqual(expected, result)

        cmds.currentUnit(time="ntsc")
        expected = 30
        result = core_scene.get_frame_rate()
        self.assertEqual(expected, result)

    def test_set_frame_rate(self):
        frame_rate_mapping = {
            23.976: "23.976fps",
            24: "film",
            25: "pal",
            29.97: "29.97fps",
            30: "ntsc",
            47.952: "47.952fps",
            48: "show",
            50: "palf",
            59.94: "59.94fps",
            60: "ntscf",
        }

        for number_fr, string_fr in frame_rate_mapping.items():
            core_scene.set_frame_rate(number_fr)
            expected = string_fr
            result = cmds.currentUnit(query=True, time=True)
            self.assertEqual(expected, result)

        for number_fr, string_fr in frame_rate_mapping.items():
            core_scene.set_frame_rate(string_fr)
            expected = string_fr
            result = cmds.currentUnit(query=True, time=True)
            self.assertEqual(expected, result)

    def test_set_frame_rate_non_listed_frame_rate(self):
        core_scene.set_frame_rate(2)
        expected = "2fps"
        result = cmds.currentUnit(query=True, time=True)
        self.assertEqual(expected, result)
        core_scene.set_frame_rate(6)
        expected = "6fps"
        result = cmds.currentUnit(query=True, time=True)
        self.assertEqual(expected, result)
        core_scene.set_frame_rate(48000)
        expected = "48000fps"
        result = cmds.currentUnit(query=True, time=True)
        self.assertEqual(expected, result)

    def test_set_frame_rate_too_high(self):
        core_scene.set_frame_rate(24)
        core_scene.set_frame_rate(48001)  # Unavailable, it will retain initial valid value
        expected = "film"
        result = cmds.currentUnit(query=True, time=True)
        self.assertEqual(expected, result)

    def test_set_frame_rate_with_fps_string(self):
        core_scene.set_frame_rate("12fps")
        expected = "12fps"
        result = cmds.currentUnit(query=True, time=True)
        self.assertEqual(expected, result)
        core_scene.set_frame_rate("120fps")
        expected = "120fps"
        result = cmds.currentUnit(query=True, time=True)
        self.assertEqual(expected, result)

    def test_get_frame_rate_changed(self):
        import_test_scene()
        maya_test_tools.set_scene_framerate(time="ntscf")
        expected = 60
        result = core_scene.get_frame_rate()
        self.assertEqual(expected, result)

    def test_get_distance_in_meters(self):
        import_test_scene()
        expected = 100
        result = core_scene.get_distance_in_meters()
        self.assertEqual(expected, result)

    def test_normalize_file_extensions(self):
        expected = (".ma", ".mb", ".fbx")
        result = core_scene._normalize_file_extensions(".MA, *.mb, or fbx")
        self.assertEqual(expected, result)

    def test_get_scene_files_filters_and_sorts_files(self):
        with tempfile.TemporaryDirectory() as directory_path:
            file_names = ["b.ma", "ignore.txt", "C.fbx", "a.mb"]
            for file_name in file_names:
                file_path = os.path.join(directory_path, file_name)
                with open(file_path, "w", encoding="utf-8") as scene_file:
                    scene_file.write("")

            expected = [
                os.path.join(directory_path, "a.mb"),
                os.path.join(directory_path, "b.ma"),
                os.path.join(directory_path, "C.fbx"),
            ]
            result = core_scene.get_scene_files(directory_path)
            self.assertEqual(expected, result)

    def test_get_adjacent_file_data(self):
        with tempfile.TemporaryDirectory() as directory_path:
            for file_name in ("a.ma", "b.ma", "c.fbx"):
                file_path = os.path.join(directory_path, file_name)
                with open(file_path, "w", encoding="utf-8") as scene_file:
                    scene_file.write("")

            current_file_path = os.path.join(directory_path, "b.ma")
            expected_previous = {
                "file_path": os.path.join(directory_path, "a.ma"),
                "position": 1,
                "total": 3,
            }
            expected_next = {
                "file_path": os.path.join(directory_path, "c.fbx"),
                "position": 3,
                "total": 3,
            }
            result_previous = core_scene.get_adjacent_file_data(
                current_file_path,
                direction=-1,
            )
            result_next = core_scene.get_adjacent_file_data(
                current_file_path,
                direction=1,
            )
        self.assertEqual(expected_previous, result_previous)
        self.assertEqual(expected_next, result_next)

        expected_loop_previous = {
            "file_path": os.path.join(directory_path, "c.fbx"),
            "position": 3,
            "total": 3,
        }
        expected_loop_next = {
            "file_path": os.path.join(directory_path, "a.ma"),
            "position": 1,
            "total": 3,
        }
        result_loop_previous = core_scene.get_adjacent_file_data(
            os.path.join(directory_path, "a.ma"),
            direction=-1,
            loop_directory=True,
        )
        result_loop_next = core_scene.get_adjacent_file_data(
            os.path.join(directory_path, "c.fbx"),
            direction=1,
            loop_directory=True,
        )

        self.assertEqual(expected_loop_previous, result_loop_previous)
        self.assertEqual(expected_loop_next, result_loop_next)

    def test_open_scene_file_unsaved_changes_choices(self):
        file_path = "C:/scene/next.ma"
        choices = (
            ("Save", False, True),
            ("Don't Save", True, True),
            ("Cancel", None, False),
        )

        for choice, expected_force, expected_result in choices:
            with patch.object(core_scene, "cmds") as mock_cmds:
                mock_cmds.file.return_value = True
                mock_cmds.confirmDialog.return_value = choice

                result = core_scene.open_scene_file(file_path, force=False)

                self.assertEqual(expected_result, result)
                mock_cmds.confirmDialog.assert_called_once()
                if expected_force is None:
                    self.assertEqual(
                        [call(query=True, modified=True)],
                        mock_cmds.file.call_args_list,
                    )
                else:
                    self.assertEqual(
                        call(file_path, open=True, force=expected_force),
                        mock_cmds.file.call_args_list[-1],
                    )

        with patch.object(core_scene, "cmds") as mock_cmds:
            result = core_scene.open_scene_file(file_path, force=True)

            self.assertTrue(result)
            mock_cmds.confirmDialog.assert_not_called()
            self.assertEqual(
                call(file_path, open=True, force=True),
                mock_cmds.file.call_args,
            )

    def test_open_adjacent_file_opens_file_and_prints_feedback(self):
        with tempfile.TemporaryDirectory() as directory_path:
            for file_name in ("a.ma", "b.ma", "c.fbx"):
                file_path = os.path.join(directory_path, file_name)
                with open(file_path, "w", encoding="utf-8") as scene_file:
                    scene_file.write("")

            current_file_path = os.path.join(directory_path, "b.ma")
            target_file_path = os.path.join(directory_path, "c.fbx")

            def _mock_file(*args, **kwargs):
                """Returns values for the mocked Maya file queries."""
                if kwargs.get("exists"):
                    return True
                if kwargs.get("expandName"):
                    return current_file_path
                return None

            with patch.object(core_scene, "cmds") as mock_cmds:
                mock_cmds.file.side_effect = _mock_file
                with patch.object(core_feedback, "FeedbackMessage") as mock_feedback:
                    result = core_scene.open_adjacent_file(direction=1, force=False)

            expected = {
                "file_path": target_file_path,
                "position": 3,
                "total": 3,
            }
            self.assertEqual(expected, result)
            self.assertEqual(
            call(target_file_path, open=True, force=False),
                mock_cmds.file.call_args_list[-1],
            )
            expected_filename_style = "color:#66CCFF;"
            expected_position_style = "color:#FFCC66;text-decoration:underline;"
            self.assertEqual(
                expected_filename_style,
                mock_feedback.call_args.kwargs["style_intro"],
            )
            self.assertEqual(
                expected_position_style,
                mock_feedback.call_args.kwargs["style_quantity"],
            )
            self.assertEqual(
                expected_position_style,
                mock_feedback.call_args.kwargs["style_pluralization"],
            )
            mock_feedback.return_value.print_inview_message.assert_called_once()
