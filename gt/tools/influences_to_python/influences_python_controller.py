"""
Extract Influence to Python Controller
"""
from gt.utils.system_utils import execute_python_code
from gt.utils.misc_utils import create_shelf_button
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.skin_utils import get_bound_joints
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class InfluencesPythonController:
    def __init__(self, view, model=None):
        """
        Initialize the InfluencesPythonController object.

        Args:
            view: The view object to interact with the user interface.
            model: The ExtractInfluenceModel object used for data manipulation.
        """
        self.model = model
        self.view = view
        self.view.controller = self

        # # Connections
        self.view.help_btn.clicked.connect(self.open_help)
        self.view.extract_influence_python_btn.clicked.connect(self.extract_influence_python)
        self.view.extract_influence_set_btn.clicked.connect(self.extract_influence_set)
        self.view.run_code_btn.clicked.connect(self.run_python_code)
        self.view.save_to_shelf_btn.clicked.connect(self.save_python_to_shelf)
        self.view.bind_skin_btn.clicked.connect(self.open_bind_skin_options)
        self.view.unbind_skin_btn.clicked.connect(self.run_unbind_skin)
        # Initial State
        self.view.non_existent_chk.setChecked(True)

        self.view.show()

    @staticmethod
    def open_help():
        """ Opens package docs """
        from gt.utils.request_utils import open_package_docs_url_in_browser
        open_package_docs_url_in_browser()

    def __extract_influence_with_validation(self, operation_target='python'):
        """
        Validation before extracting python or set out of the bound mesh
        Args:
            operation_target (optional, string): "python" will output python code into the python output box,
                                                 "set" will create selection sets
        Returns:
            str or None: Returns the code to select influence joints or None there was an issue or creating a set.
        """
        import maya.cmds as cmds
        selection = cmds.ls(selection=True) or []

        if len(selection) == 0:
            cmds.warning('Nothing selected. Please select a bound mesh and try again.')
            return

        valid_nodes = []
        for sel in selection:
            shapes = cmds.listRelatives(sel, shapes=True, children=False) or []
            if shapes:
                if cmds.objectType(shapes[0]) == 'mesh' or cmds.objectType(shapes[0]) == 'nurbsSurface':
                    valid_nodes.append(sel)

        if operation_target == 'python':
            commands = []
            for transform in valid_nodes:
                message = '# Joint influences found in "' + transform + '":'
                message += '\nbound_list = '
                bound_joints = get_bound_joints(transform)

                if not bound_joints:
                    cmds.warning('Unable to find skinCluster for "' + transform + '".')
                    continue

                if self.view.include_mesh_chk.isChecked():
                    bound_joints.insert(0, transform)

                message += str(bound_joints)

                if self.view.non_existent_chk.isChecked():
                    message += '\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]'

                message += '\ncmds.select(bound_list)'

                commands.append(message)

            _code = ''
            for cmd in commands:
                _code += cmd + '\n\n'
            if _code.endswith('\n\n'):  # Removes unnecessary spaces at the end
                _code = _code[:-2]
            return _code

        if operation_target == 'set':
            for transform in valid_nodes:
                bound_joints = get_bound_joints(transform)
                if self.view.include_mesh_chk.isChecked():
                    bound_joints.insert(0, transform)
                new_set = cmds.sets(name=transform + "_influenceSet", empty=True)
                for jnt in bound_joints:
                    cmds.sets(jnt, add=new_set)

    def extract_influence_python(self):
        """
        Extracts the TRS channels as setAttr commands and populates the python output box with the extracted content.
        """
        _code = "import maya.cmds as cmds\n\n"
        _code += self.__extract_influence_with_validation(operation_target='python')
        self.view.clear_python_output()
        self.view.set_python_output_text(text=_code)

    def extract_influence_set(self):
        """
        Extracts the TRS channels as lists and populates the python output box with the extracted content.
        """
        self.__extract_influence_with_validation(operation_target='set')

    def run_python_code(self):
        """
        Attempts to run the code found in the "Python Output" box.
        """
        _code = self.view.get_python_output_text()
        execute_python_code(code=_code, user_maya_warning=True)

    def save_python_to_shelf(self):
        """
        Saves the content of the python output box to a shelf button.
        """
        import maya.cmds as cmds
        _code = self.view.get_python_output_text()
        if _code:
            create_shelf_button(_code,
                                label='setAttr',
                                tooltip='Extracted Attributes',
                                image="editRenderPass.png",
                                label_color=(0, .84, .81))

            highlight_style = "color:#FF0000;text-decoration:underline;"
            feedback = FeedbackMessage(prefix='Python code',
                                       style_prefix=highlight_style,
                                       conclusion='was added as a button to your current shelf.')
            feedback.print_inview_message()
        else:
            cmds.warning('Unable to save to shelf. "Output Python Code" is empty.')

    @staticmethod
    def open_bind_skin_options():
        """ Runs the mel command to open the bind skin options """
        import maya.mel as mel
        mel.eval('SmoothBindSkinOptions;')

    @staticmethod
    def run_unbind_skin():
        """ Runs the mel command unbind skins """
        import maya.mel as mel
        mel.eval('DetachSkin;')


if __name__ == "__main__":
    print('Run it from "__init__.py".')
