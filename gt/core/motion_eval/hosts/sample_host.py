"""
Motion Evaluation Sample Host - Evaluates motion sample files (.motion.json) in plain Python.

No DCC is needed: the "scene" is a sample saved by sample_io. Every frame range mode
returns the sample's own range, every node counts as animated, and nodes listed in the
sample's "joints" are the joints.
"""

from .host_base import SceneHost
from .. import sample_io


class SampleHost(SceneHost):
    """Scene host that reads motion sample files instead of a DCC scene."""

    name = "sample"
    label = "Python (motion samples)"
    scene_extensions = (sample_io.SAMPLE_EXTENSION,)
    copy_extension = ""
    joint_label = "joint"
    supports_selection = False
    supports_score_write = False

    def __init__(self, sample=None, file_path=""):
        """Starts with an optional sample already loaded.

        Args:
            sample (dict, optional): Sample to serve (for example built in memory).
            file_path (str, optional): Where the sample came from.
        """
        self.sample = sample
        self.file_path = file_path

    def is_available(self):
        """Plain Python is always available.

        Returns:
            bool: True.
        """
        return True

    def is_running(self):
        """Plain Python is always running.

        Returns:
            bool: True.
        """
        return True

    # ------------------------------------------------ Files ------------------------------------------------
    def load_scene(self, file_path, load_mode="open", align_up_axis=True):
        """Loads a motion sample file.

        Args:
            file_path (str): Motion sample path.
            load_mode (str): Unused.
            align_up_axis (bool): Unused (the sample records its up axis).

        Returns:
            dict: "frame_range" and "fps" of the sample.
        """
        self.sample = sample_io.load_sample(file_path)
        self.file_path = str(file_path)
        return {"frame_range": self.get_time_range("animation"), "fps": self.get_fps()}

    def get_loaded_sample(self):
        """Gets the loaded sample.

        Returns:
            dict: Sample.

        Raises:
            ValueError: If no sample is loaded.
        """
        if not self.sample:
            raise ValueError("No motion sample is loaded.")
        return self.sample

    def get_scene_path(self):
        """Gets the loaded sample path.

        Returns:
            str: Path or "".
        """
        return self.file_path

    # ------------------------------------------------ Scene Info ------------------------------------------------
    def get_fps(self):
        """Gets the sample frame rate.

        Returns:
            float: Frames per second.
        """
        return float(self.get_loaded_sample().get("fps") or 30.0)

    def get_meters_per_unit(self):
        """Gets the sample unit size.

        Returns:
            float: Meters per unit.
        """
        return float(self.get_loaded_sample().get("meters_per_unit") or 0.01)

    def get_up_axis(self):
        """Gets the sample up axis.

        Returns:
            str: "y" or "z".
        """
        return str(self.get_loaded_sample().get("up_axis") or "y").lower()

    def get_time_range(self, kind):
        """Gets the sample frame range (the same for every kind).

        Args:
            kind (str): Ignored.

        Returns:
            tuple: (start, end) frames.
        """
        sample = self.get_loaded_sample()
        start = int(sample.get("start_frame") or 0)
        return float(start), float(start + int(sample.get("frame_count") or 1) - 1)

    def get_key_range(self, node_paths):
        """Gets the sample frame range when any of the nodes exist.

        Args:
            node_paths (list): Node paths.

        Returns:
            tuple or None: (start, end) frames.
        """
        nodes = self.get_loaded_sample().get("nodes") or {}
        return self.get_time_range("animation") if any(path in nodes for path in node_paths) else None

    # ------------------------------------------------ Nodes ------------------------------------------------
    def list_joints(self):
        """Lists the sample's joints.

        Returns:
            list: Node paths.
        """
        sample = self.get_loaded_sample()
        nodes = sample.get("nodes") or {}
        return [path for path in sample.get("joints") or sorted(nodes) if path in nodes]

    def list_transforms(self):
        """Lists sample nodes that are not joints.

        Returns:
            list: Node paths.
        """
        joints = set(self.list_joints())
        return [path for path in sorted(self.get_loaded_sample().get("nodes") or {}) if path not in joints]

    def list_animated_nodes(self):
        """Lists every sample node.

        Returns:
            list: Sorted node paths.
        """
        return sorted(self.get_loaded_sample().get("nodes") or {})

    def get_parents(self, node_paths):
        """Gets the recorded parent of each node.

        Args:
            node_paths (list): Node paths.

        Returns:
            dict: Node path to parent path (or None).
        """
        nodes = self.get_loaded_sample().get("nodes") or {}
        return {path: (nodes.get(path) or {}).get("parent") for path in node_paths}

    def get_extra_data(self, data_key, node_paths, start_frame, end_frame):
        """Returns extra data stored in the motion sample file under "extra".

        Args:
            data_key (str): Extra data key.
            node_paths (list): Unused.
            start_frame (int): Unused.
            end_frame (int): Unused.

        Returns:
            object or None: Stored data.
        """
        return (self.get_loaded_sample().get("extra") or {}).get(data_key)

    def sample_world_matrices(self, node_paths, start_frame, end_frame):
        """Returns the recorded matrices of a frame range.

        Args:
            node_paths (list): Node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame.

        Returns:
            dict: Node path to a list of flat 16-value matrices.

        Raises:
            ValueError: If the range is outside the sample.
        """
        sample = self.get_loaded_sample()
        first, last = self.get_time_range("animation")
        if int(start_frame) < int(first) or int(end_frame) > int(last):
            raise ValueError(f"Frames {start_frame}-{end_frame} are outside the sample range {first:g}-{last:g}.")
        offset = int(start_frame) - int(first)
        count = int(end_frame) - int(start_frame) + 1
        nodes = sample.get("nodes") or {}
        return {path: [list(matrix) for matrix in nodes[path]["matrices"][offset:offset + count]]
                for path in node_paths}
