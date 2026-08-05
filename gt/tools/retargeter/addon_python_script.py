"""
Animation Retargeter Addon: Post Bake
"""

import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AddonPythonScript(tools_rt_frm.TargetingAddon):
    __version__ = "0.0.1-alpha"
    allow_multiple = True

    def __init__(self, name=None):
        """
        Initiates the post bake process
        Args:
            name (str, optional): A name for the module.
        """
        if not name:
            name = "Python Script"
        super().__init__(name=name)
        self.execution_order = self.Order.post_retarget
        self.active = True
        self.code = ""

    def set_active(self, active):
        """
        Sets the active state.
        Args:
            active (bool): The active state of the addon.
        """
        self.active = active

    def get_active(self):
        """
        Gets the active state for this addon.
        Returns:
            bool: The active state of the addon.
        """
        return self.active

    def apply_addon(self):
        """
        Executes stored python code.
        """
        import gt.utils.system as utils_sys

        if self.code and self.active:
            utils_sys.execute_python_code(
                code=self.code,
                custom_logger=logger,
                use_maya_warning=False,
                log_level=logging.WARNING,
                verbose=True,
                import_cmds=True,
                exec_globals=globals,
                raise_errors=False,
            )
