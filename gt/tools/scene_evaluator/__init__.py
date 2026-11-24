"""Scene Evaluator tool entry point."""

__version_tuple__ = (1, 0, 0)
__version__ = ".".join(str(number) for number in __version_tuple__)


def launch_tool():
    """Creates and shows Scene Evaluator.

    Returns:
        SceneEvaluatorController: Controller retained by the window.
    """
    from gt.core.prefs import Prefs
    from gt.tools.scene_evaluator.scene_evaluator_controller import SceneEvaluatorController
    from gt.tools.scene_evaluator.scene_evaluator_model import SceneEvaluatorModel
    from gt.tools.scene_evaluator.scene_evaluator_view import SceneEvaluatorView
    from gt.ui.qt_utils import QtApplicationContext

    with QtApplicationContext() as context:
        view = SceneEvaluatorView(parent=context.get_parent(), version=__version__)
        model = SceneEvaluatorModel(prefs=Prefs("scene_evaluator_prefs"))
        return SceneEvaluatorController(model=model, view=view)


if __name__ == "__main__":
    launch_tool()
