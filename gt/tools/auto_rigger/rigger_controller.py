"""
Auto Rigger Controller
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerController:
    def __init__(self, model, view):
        """
        Initialize the RiggerController object.

        Args:
            model: The RiggerModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self

        # Connections
        self.view.show()

    def get_selected_module(self):
        pass

    def populate_module_tree(self):
        self.view.clear_module_tree()

    def save_project(self):
        pass

    def load_project(self):
        pass


if __name__ == "__main__":
    print('Run it from "__init__.py".')
