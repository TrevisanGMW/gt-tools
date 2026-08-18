"""Copy/Paste Animation tool entry point."""

__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Copy/Paste Animation MVC tool.

    Returns:
        AnimCopyPasteController: Launched controller.
    """
    from gt.tools.anim_copy_paste.anim_copy_paste_controller import AnimCopyPasteController
    from gt.tools.anim_copy_paste.anim_copy_paste_model import AnimCopyPasteModel
    from gt.tools.anim_copy_paste.anim_copy_paste_service import AnimCopyPasteService
    from gt.tools.anim_copy_paste.anim_copy_paste_view import AnimCopyPasteView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = AnimCopyPasteModel()
        view = AnimCopyPasteView(parent=context.get_parent(), version=__version__)
        service = AnimCopyPasteService()
        return AnimCopyPasteController(model=model, view=view, service=service)


if __name__ == "__main__":
    launch_tool()
