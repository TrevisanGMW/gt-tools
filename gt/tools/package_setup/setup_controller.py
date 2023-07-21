"""
Package Setup Controller (Connections))
"""
import logging

logger = logging.getLogger(__name__)


class PackageSetupController:
    def __init__(self, model, view):
        """
        Initializes package setup model object and creates connections between model and view
        Args:
            model (PackageSetupModel): Setup Logic
            view (PackageSetupView): Setup UI
        """
        self.model = model
        self.view = view

        self.view.controller = self.model  # To avoid garbage collection

        # Buttons
        self.view.ButtonInstallClicked.connect(self.model.install_package)
        self.view.ButtonUninstallClicked.connect(self.model.uninstall_package)
        self.view.ButtonRunOnlyClicked.connect(self.model.run_only_package)

        # Feedback
        self.model.UpdatePath.connect(self.view.update_installation_path_text_field)
        self.model.UpdateVersion.connect(self.view.update_version_texts)
        self.model.UpdateStatus.connect(self.view.update_status_text)
        self.model.CloseView.connect(self.view.close_window)

        # Initial Update
        self.model.update_path()
        self.model.update_version()
        self.model.update_status()


if __name__ == "__main__":
    controller = PackageSetupController(None, None)
