"""Tests for editable batch processor script resources."""

import unittest

from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks.task_external_blender import DEFAULT_BLENDER_INLINE_SCRIPT
from gt.tools.batch_processor.tasks.task_external_mobu import DEFAULT_MOBU_INLINE_SCRIPT
from gt.tools.batch_processor.tasks.task_external_unreal import DEFAULT_UNREAL_INLINE_SCRIPT
from gt.tools.batch_processor.tasks.task_hik_retarget import DEFAULT_POST_SCRIPT_TEXT as HIK_POST_SCRIPT_TEXT
from gt.tools.batch_processor.tasks.task_hik_retarget import DEFAULT_PRE_BAKE_SCRIPT_TEXT
from gt.tools.batch_processor.tasks.task_maya_import import DEFAULT_POST_SCRIPT_TEXT as MAYA_POST_SCRIPT_TEXT
from gt.tools.batch_processor.tasks.task_python_script import DEFAULT_PYTHON_INLINE_SCRIPT


class TestBatchProcessorScripts(unittest.TestCase):
    """Tests that task script variables load their editable source files."""

    def test_script_variables_match_script_files(self):
        """Ensures each script variable exposes its complete file contents."""
        script_values = (
            (
                "script_inline_external_blender.py",
                DEFAULT_BLENDER_INLINE_SCRIPT,
            ),
            (
                "script_inline_external_mobu.py",
                DEFAULT_MOBU_INLINE_SCRIPT,
            ),
            (
                "script_inline_external_unreal.py",
                DEFAULT_UNREAL_INLINE_SCRIPT,
            ),
            (
                "script_pre_bake_hik_retarget.py",
                DEFAULT_PRE_BAKE_SCRIPT_TEXT,
            ),
            (
                "script_post_hik_retarget.py",
                HIK_POST_SCRIPT_TEXT,
            ),
            (
                "script_post_maya_import.py",
                MAYA_POST_SCRIPT_TEXT,
            ),
            (
                "script_inline_python_script.py",
                DEFAULT_PYTHON_INLINE_SCRIPT,
            ),
        )

        for script_name, script_value in script_values:
            expected_script = task_utils.load_script(script_name)
            self.assertEqual(expected_script, script_value)
