"""Controller for Animation Label Tracker."""

class AnimationLabelTrackerController:
    """Connects the Animation Label Tracker model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (AnimationLabelTrackerModel): Tracker model.
            view (AnimationLabelTrackerView): Tracker view.
        """
        self.model = model
        self.view = view
        self.view.controller = self

    def start(self):
        """Shows and activates the tracker window.

        Returns:
            AnimationLabelTrackerController: This controller.
        """
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
        return self

