"""Connect Attributes tool entry point."""

__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Connect Attributes MVC tool.

    Returns:
        ConnectAttributesController: Launched controller.
    """
    from gt.tools.connect_attributes.connect_attributes_controller import ConnectAttributesController
    from gt.tools.connect_attributes.connect_attributes_model import ConnectAttributesModel
    from gt.tools.connect_attributes.connect_attributes_service import ConnectAttributesService
    from gt.tools.connect_attributes.connect_attributes_view import ConnectAttributesView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = ConnectAttributesModel()
        view = ConnectAttributesView(parent=context.get_parent(), version=__version__)
        service = ConnectAttributesService()
        return ConnectAttributesController(model=model, view=view, service=service)


if __name__ == "__main__":
    launch_tool()
