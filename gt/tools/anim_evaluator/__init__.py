"""
Animation Evaluator - Scores animation quality with configurable checks and skeleton templates.
2026-11-03
"""

__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Creates and displays the Animation Evaluator MVC components.

    Returns:
        AnimEvaluatorController: Controller retained by the window.
    """
    from gt.tools.anim_evaluator.anim_evaluator_controller import AnimEvaluatorController
    from gt.tools.anim_evaluator.anim_evaluator_model import AnimEvaluatorModel
    from gt.tools.anim_evaluator.anim_evaluator_view import AnimEvaluatorView
    from gt.ui.qt_utils import QtApplicationContext

    with QtApplicationContext() as context:
        view = AnimEvaluatorView(parent=context.get_parent(), version=__version__)
        return AnimEvaluatorController(AnimEvaluatorModel(), view)


if __name__ == "__main__":
    launch_tool()
