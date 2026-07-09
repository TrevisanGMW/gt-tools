import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import logging
import os


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleRBFPoseLoader(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_pose_wrangler
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="RBF Pose Loader", prefix=None, suffix=None):
        """
        Args:
            name (str): Module name.
            prefix (str or None): Optional naming prefix.
            suffix (str or None): Optional naming suffix.
        """

        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.code = tools_rig_frm.CodeData()
        self.code.set_order(tools_rig_frm.CodeData.Order.post_build)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.file_path = r"{project-dir}/rbf/{project-name}.json"
        self.set_extra_callable_function(self.load_rbf_json, order=tools_rig_frm.CodeData.Order.post_build)

    def set_file_path(self, file_path=None):
        """
        Sets the path used to import a file.
        Args:
            file_path (str): A file path to be imported. it overwrites the value even if an empty string.
        """
        if file_path is None:
            self.file_path = ""
        if not isinstance(file_path, str):
            logger.warning("Unable to set file path. Invalid data type was provided.")
            return
        _parsed_path = self.parse_path(path=file_path)
        self.file_path = _parsed_path

    def load_rbf_json(self):
        """
        Loads the Json containing the RBF poses
        """
        import PoseWrangler.epic_pose_wrangler.v2.main as pose_wrangler

        _parsed_path = self.parse_path(path=self.file_path)
        self.warn_if_path_outside_project(_parsed_path)

        # Check the path exists
        if not os.path.exists(_parsed_path):
            logger.warning("Unable to use provided file path. Target file does not exist.")
            return
        try:
            tools_rig_utils.set_rig_apose()
        except:
            logger.warning("Unable to set rig A Pose, please check the pose wrangler is functioning correctly.")

        pose_wrangler.UERBFAPI().deserialize_from_file(file_path=_parsed_path)

        try:
            tools_rig_utils.set_rig_tpose()
        except:
            logger.warning("Unable to set rig T Pose, please check the pose wrangler is functioning correctly.")
