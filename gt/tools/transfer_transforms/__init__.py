"""Transfer Transforms tool entry point."""

__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Transfer Transforms MVC tool.

    Returns:
        TransferTransformsController: Launched controller.
    """
    from gt.tools.transfer_transforms.transfer_transforms_controller import TransferTransformsController
    from gt.tools.transfer_transforms.transfer_transforms_model import TransferTransformsModel
    from gt.tools.transfer_transforms.transfer_transforms_service import TransferTransformsService
    from gt.tools.transfer_transforms.transfer_transforms_view import TransferTransformsView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = TransferTransformsModel()
        view = TransferTransformsView(parent=context.get_parent(), version=__version__)
        service = TransferTransformsService()
        return TransferTransformsController(
            model=model,
            view=view,
            service=service,
            version=__version__,
        )


if __name__ == "__main__":
    launch_tool()
