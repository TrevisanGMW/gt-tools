"""
 GT Morphing to Attributes (a.k.a. Blend Shapes to Attributes)
 github.com/TrevisanGMW/gt-tools - 2022-03-17

 Creates driver attributes on a control object so blend shape (morphing) targets
 can be animated without selecting the deformed mesh.
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Morphing Attributes.
    Creates Model, View and Controller.

    Returns:
        MorphingAttributesController: Controller for the launched tool.
    """
    from gt.tools.morphing_attributes import morphing_attributes_controller
    from gt.tools.morphing_attributes import morphing_attributes_model
    from gt.tools.morphing_attributes import morphing_attributes_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = morphing_attributes_view.MorphingAttributesView(parent=context.get_parent(), version=__version__)
        model = morphing_attributes_model.MorphingAttributesModel()
        controller = morphing_attributes_controller.MorphingAttributesController(model=model, view=view)
        return controller


if __name__ == "__main__":
    launch_tool()
