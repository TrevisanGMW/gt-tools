"""Controller for Annotation Tracker."""

class AnnotationTrackerController:
    """Connects the Annotation Tracker model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (AnnotationTrackerModel): Tracker model.
            view (AnnotationTrackerView): Tracker view.
        """
        self.model = model
        self.view = view
        self.view.controller = self

    def start(self):
        """Shows and activates the tracker window.

        Returns:
            AnnotationTrackerController: This controller.
        """
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
        return self

