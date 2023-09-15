"""
Extract Influence to Python Controller
"""
from gt.utils.skin_utils import selected_get_python_influences_code, selected_add_influences_to_set
from gt.utils.system_utils import execute_python_code
from gt.utils.misc_utils import create_shelf_button
from gt.utils.feedback_utils import FeedbackMessage
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

    def extract_influence_python(self):
        """
        Extracts the TRS channels as setAttr commands and populates the python output box with the extracted content.
        """
        include_bound_mesh = self.view.include_mesh_chk.isChecked()
        include_existing_filter = self.view.non_existent_chk.isChecked()
        _maya_import = "import maya.cmds as cmds\n\n"
        _code = selected_get_python_influences_code(include_bound_mesh=include_bound_mesh,
                                                    include_existing_filter=include_existing_filter)
        if _code:
            _code = _maya_import + _code
            self.view.clear_python_output()
            self.view.set_python_output_text(text=_code)

    @staticmethod
    def extract_influence_set():
        """
        Extracts the TRS channels as lists and populates the python output box with the extracted content.
        """
        created_sets = selected_add_influences_to_set() or []
        feedback = FeedbackMessage(quantity=len(created_sets),
                                   singular="selection set was",
                                   plural="selection sets were",
                                   conclusion="created.",
                                   zero_overwrite_message='No selection set was created.')
        feedback.print_inview_message()

    def run_python_code(self):
        """
        Attempts to run the code found in the "Python Output" box.
        """
        _code = self.view.get_python_output_text()
        execute_python_code(code=_code, use_maya_warning=True, import_cmds=True)

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
