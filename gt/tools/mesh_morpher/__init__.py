"""
Mesh Morpher
"""

from gt.utils.dependency import ensure_dependencies
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (0, 0, 2)
__version_suffix__ = "alpha"
__version__ = ".".join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launches Mesh Morpher after validating its scientific dependencies.

    Returns:
        MorpherController or None: Launched controller, or None when dependency
            installation is declined or unsuccessful.
    """
    dependencies = {"numpy": "numpy", "scipy": "scipy"}
    if not ensure_dependencies(dependencies):
        logger.warning("Mesh Morpher requires NumPy and SciPy. Launch was cancelled.")
        return None

    from gt.tools.mesh_morpher import morpher_controller
    from gt.tools.mesh_morpher import morpher_model
    from gt.tools.mesh_morpher import morpher_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        _view = morpher_view.MorpherView(parent=context.get_parent(), version=__version__)
        _model = morpher_model.MorpherModel()
        _controller = morpher_controller.MorpherController(model=_model, view=_view)
        return _controller


if __name__ == "__main__":
    launch_tool()
