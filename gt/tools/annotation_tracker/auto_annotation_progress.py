"""Responsive progress for interactive annotation, with Maya calls on its main thread."""

import time
from concurrent.futures import ThreadPoolExecutor

from gt.ui.qt_import import QtCore, QtWidgets


class OperationCancelled(RuntimeError):
    """Raised when the user cancels while waiting for a network operation."""


class AnnotationProgress(QtWidgets.QDialog):
    """Shows progress while Maya captures frames or waits for a network operation."""

    def __init__(self, parent):
        """Creates a short-lived progress window.

        Args:
            parent (QWidget): Annotation Tracker or Setup window.
        """
        super().__init__(parent)
        self.setWindowTitle("Auto Annotate")
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog
            | QtCore.Qt.WindowType.CustomizeWindowHint
            | QtCore.Qt.WindowType.WindowTitleHint
        )
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(480)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)
        self.setSizeGripEnabled(False)
        self.message = QtWidgets.QLabel()
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(self.message.fontMetrics().lineSpacing() * 2 + 6)
        self.message.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.bar = QtWidgets.QProgressBar()
        self.bar.setMinimumHeight(max(22, self.bar.fontMetrics().height() + 8))
        self.bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setToolTip("Stops waiting. Results from finished requests are kept.")
        self.cancel_button.clicked.connect(self.request_cancel)
        self.cancelled = False
        self.label = ""
        self.opened_at = time.monotonic()
        self.step_started = self.opened_at
        layout.addWidget(self.message)
        layout.addWidget(self.bar)
        layout.addWidget(self.cancel_button, 0, QtCore.Qt.AlignmentFlag.AlignRight)

    def __enter__(self):
        """Shows the progress window.

        Returns:
            AnnotationProgress: Active progress window.
        """
        self.opened_at = self.step_started = time.monotonic()
        self.show()
        return self

    def __exit__(self, exc_type, exception, traceback):
        """Closes progress after success or failure.

        Args:
            exc_type (type or None): Exception type.
            exception (Exception or None): Raised exception.
            traceback (object or None): Exception traceback.
        """
        self.done(0)
        self.deleteLater()

    def request_cancel(self):
        """Marks the run as cancelled and stops waiting for the current operation."""
        self.cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling…")

    @staticmethod
    def _clock(seconds):
        """Formats seconds as minutes and seconds.

        Args:
            seconds (float): Duration.

        Returns:
            str: Text such as ``02:05``.
        """
        return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"

    def _show_elapsed(self):
        """Shows the stage text with total and current-step elapsed time."""
        now = time.monotonic()
        self.message.setText(
            f"{self.label}\nElapsed {self._clock(now - self.opened_at)} · this step {self._clock(now - self.step_started)}"
        )

    def reject(self):
        """Leaves progress visible until its operation completes."""

    def update_stage(self, text, completed=0, total=0):
        """Updates and paints an operation phase.

        Args:
            text (str): Current phase.
            completed (int): Completed frames for determinate phases.
            total (int): Total frames, or zero while awaiting the provider.
        """
        if text != self.label:
            self.step_started = time.monotonic()
        self.label = text
        self._show_elapsed()
        self.adjustSize()
        self.bar.setRange(0, total)
        self.bar.setValue(completed)
        QtCore.QCoreApplication.processEvents()

    def wait_for_network(self, label, function, *args, **kwargs):
        """Runs network or CLI work off the Maya thread while keeping progress responsive.

        Args:
            label (str): Progress message while waiting.
            function (callable): Operation containing only network or subprocess work.
            *args: Positional arguments to the operation.
            **kwargs: Named arguments to the operation.

        Returns:
            object: Result of the background operation.
        """
        self.update_stage(label, self.bar.value(), self.bar.maximum())
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer(self)
        timer.setInterval(40)

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="annotation_io")
        try:
            future = executor.submit(function, *args, **kwargs)

            def finish_when_ready():
                """Stops the local Qt wait when the worker finishes or the user cancels, and keeps the clock moving."""
                if future.done() or self.cancelled:
                    loop.quit()
                else:
                    self._show_elapsed()

            timer.timeout.connect(finish_when_ready)
            if not future.done():
                timer.start()
                try:
                    execute_loop = getattr(loop, "exec", None) or loop.exec_
                    execute_loop()
                finally:
                    timer.stop()
                    timer.deleteLater()
            else:
                timer.deleteLater()
            if self.cancelled and not future.done():
                raise OperationCancelled("Cancelled by the user.")
            return future.result()
        finally:
            executor.shutdown(wait=False)
