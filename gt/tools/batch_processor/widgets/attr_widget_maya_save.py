"""
Batch Processor Maya Save Task Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask


class AttrWidgetMayaSaveTask(AttrWidgetTask):
    """Attribute widget for the Maya save task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Maya save task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (MayaSaveTask, optional): Maya save task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings(
            scene_io_settings={
                "load_mode_key": "source_load_mode",
                "output_extension_key": "output_extension",
                "output_extension_values": [".ma", ".mb"],
            }
        )
        self.content_layout.addStretch()
