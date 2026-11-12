"""
Motion Evaluation Host Base - The small interface every scene host (Maya, Blender, ...) implements.

A host is the only code that talks to a DCC. Everything above it (sampling, evaluation,
checks, scoring, outputs, runner) only calls these methods, so a check written once runs
in every host. A host never computes anything about motion quality.

Conventions every host must follow:
    Node paths: strings shaped like Maya long DAG paths ("|group|Hips|Spine"). The last
        "|" part is the node's own name and may carry a "namespace:" prefix. Templates
        match roles on that last part (see templates.split_node_name).
    Matrices: flat lists of 16 floats in Maya's row-major, row-vector layout: the
        translation is at indices 12, 13, 14 and rows 0-2 are the scaled X, Y, Z axes.
        Hosts with column-vector math (Blender) transpose before flattening.
    Units: world matrices are in scene units; get_meters_per_unit says how big one is.
    Frames: whole frame numbers in the host's own frame rate.

To add a host: subclass SceneHost, implement every method that raises
NotImplementedError, set the class attributes, and register it in hosts/__init__.py.
"""

import contextlib
import fnmatch
import sys


class SceneHost:
    """Base class of a scene host. Subclasses override the methods marked "Required"."""

    name = ""
    label = ""
    scene_extensions = ()
    copy_extension = ""
    joint_label = "joint"
    supports_selection = False
    supports_score_write = False

    # ------------------------------------------------ Session ------------------------------------------------
    def is_available(self):
        """Checks whether this host's Python modules can be imported in this process.

        Returns:
            bool: True when the host can be used (possibly after session() starts it).
        """
        return False

    def is_running(self):
        """Checks whether the host is already running in this process.

        Returns:
            bool: True when scene calls work right away.
        """
        return False

    @contextlib.contextmanager
    def session(self, quiet=False):
        """Starts the host when needed and stops it afterwards.

        Args:
            quiet (bool): Hide the host's startup and shutdown messages.

        Yields:
            bool: True when this context started the host.
        """
        yield False

    def get_unavailable_message(self):
        """Explains how to run this host when it is not available in this Python.

        Returns:
            str: Message for the user.
        """
        return f"{self.label} is not available in this Python ({sys.executable})."

    # ------------------------------------------------ Files ------------------------------------------------
    def can_load(self, file_path):
        """Checks whether this host can load a file, by extension.

        Args:
            file_path (str): File path.

        Returns:
            bool: True when the extension is in scene_extensions.
        """
        return str(file_path).lower().endswith(tuple(self.scene_extensions))

    def load_scene(self, file_path, load_mode="open", align_up_axis=True):
        """Required. Replaces the current scene with a file, ready to sample.

        Args:
            file_path (str): Scene path.
            load_mode (str): "open" or "import" (into a new empty scene) when the host supports both.
            align_up_axis (bool): Rotate files with another up axis into the scene's up axis when the
                host needs it.

        Returns:
            dict: Host-specific load information (may be empty).
        """
        raise NotImplementedError

    def save_scene_copy(self, target_path):
        """Required when copy_extension is set. Saves the open scene to a new file.

        Args:
            target_path (str): Destination path ending with copy_extension.
        """
        raise NotImplementedError

    def get_scene_path(self):
        """Required. Gets the path of the open scene.

        Returns:
            str: Scene path, or "" for unsaved scenes.
        """
        raise NotImplementedError

    # ------------------------------------------------ Scene Info ------------------------------------------------
    def get_fps(self):
        """Required. Gets the scene frame rate.

        Returns:
            float: Frames per second.
        """
        raise NotImplementedError

    def get_meters_per_unit(self):
        """Required. Gets the size of one scene unit in meters.

        Returns:
            float: Meters per scene unit.
        """
        raise NotImplementedError

    def get_up_axis(self):
        """Required. Gets the scene up axis.

        Returns:
            str: "y" or "z".
        """
        raise NotImplementedError

    def get_time_range(self, kind):
        """Required. Gets a scene frame range.

        Args:
            kind (str): "playback" (the inner range the user plays) or "animation" (the full outer range).

        Returns:
            tuple: (start, end) frames as floats.
        """
        raise NotImplementedError

    def get_key_range(self, node_paths):
        """Required. Gets the first and last keyframe on some nodes.

        Args:
            node_paths (list): Node paths.

        Returns:
            tuple or None: (start, end) frames, or None when the nodes have no keys.
        """
        raise NotImplementedError

    # ------------------------------------------------ Nodes ------------------------------------------------
    def list_joints(self):
        """Required. Lists every joint (Maya joints, Blender bones).

        Returns:
            list: Node paths.
        """
        raise NotImplementedError

    def list_transforms(self):
        """Required. Lists the transforms that are not joints.

        Returns:
            list: Node paths.
        """
        raise NotImplementedError

    def list_animated_nodes(self):
        """Required. Lists joints and transforms driven directly by animation curves.

        Returns:
            list: Sorted node paths.
        """
        raise NotImplementedError

    def find_nodes(self, pattern):
        """Finds joints and transforms whose own name matches a wildcard pattern.

        Hosts with their own name search (Maya's ls) override this.

        Args:
            pattern (str): Name or wildcard such as "*:root" or "prop_ctrl".

        Returns:
            list: Matching node paths.
        """
        pattern = str(pattern).strip()
        if not pattern:
            return []
        matches = []
        for node_path in self.list_joints() + self.list_transforms():
            short_name = node_path.split("|")[-1]
            if fnmatch.fnmatchcase(short_name, pattern) or fnmatch.fnmatchcase(node_path, pattern):
                matches.append(node_path)
        return matches

    def get_selected_nodes(self):
        """Gets the selected joints and transforms (only hosts with supports_selection).

        Returns:
            list: Node paths.
        """
        return []

    def get_parents(self, node_paths):
        """Required. Gets the direct parent of each node.

        Args:
            node_paths (list): Node paths.

        Returns:
            dict: Node path to parent path, or None for top-level nodes.
        """
        raise NotImplementedError

    def sample_world_matrices(self, node_paths, start_frame, end_frame):
        """Required. Samples the world matrix of every node on every frame.

        The host's current frame is restored afterwards.

        Args:
            node_paths (list): Node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame (included).

        Returns:
            dict: Node path to a list of flat 16-value matrices (see the module docstring).
        """
        raise NotImplementedError

    def get_extra_data(self, data_key, node_paths, start_frame, end_frame):
        """Collects extra scene data for checks that declare required_data (optional).

        Return JSON-compatible data (lists, dictionaries, numbers) so motion samples can store it.
        Hosts override this and handle the keys they support; every other key returns None, which
        makes the checks that need it skip with a reason.

        Args:
            data_key (str): Extra data key, for example "floor_heights".
            node_paths (list): Sampled node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame.

        Returns:
            object or None: Data, or None when this host cannot provide the key.
        """
        return None

    # ------------------------------------------------ Keying (repairs) ---------------------------------------
    supports_keying = False

    def edit_block(self, label="motion_eval_repair"):
        """Optional. Groups scene edits (for example into one undo step).

        Args:
            label (str): Name of the edit group.

        Returns:
            contextlib.AbstractContextManager: Context manager around the edits.
        """
        return contextlib.nullcontext()

    def key_local_transforms(self, node_path, frames, local_matrices, channels=("rotate",)):
        """Optional (needed by repairs). Keys a node's local transform on the given frames.

        Args:
            node_path (str): Node path.
            frames (list): Whole frame numbers.
            local_matrices (list): One flat 16-value local matrix (child-in-parent space) per frame.
            channels (tuple): "rotate" and/or "translate".

        Returns:
            dict: {"keys": int keys set, "warnings": list of str}.
        """
        raise NotImplementedError(f"The {self.label or self.name} host cannot write keys.")

    # ------------------------------------------------ Score Storage ------------------------------------------
    def find_score_holder(self, target_mode, node_name, roles=None, create=True):
        """Finds (and optionally creates) the object that stores the score (supports_score_write hosts).

        Args:
            target_mode (str): scene_io.TARGET_DEDICATED_NODE, TARGET_ROLE, or TARGET_NAMED_NODE.
            node_name (str): Dedicated node name, role key, or node name depending on the mode.
            roles (dict, optional): Resolved role to node path mapping (role mode).
            create (bool): Create the dedicated holder when missing.

        Returns:
            str or None: Holder name or path, or None when missing and not created.

        Raises:
            ValueError: If the target cannot be used.
        """
        raise NotImplementedError(f"{self.label} cannot store scores in the scene.")

    def read_score_value(self, holder, attribute_name):
        """Reads an integer score stored on a holder.

        Args:
            holder (str): Holder from find_score_holder.
            attribute_name (str): Attribute or property name.

        Returns:
            int or None: Stored score, or None when missing.
        """
        raise NotImplementedError(f"{self.label} cannot store scores in the scene.")

    def write_score_values(self, holder, score_attribute, score, report_attribute="", report_text=""):
        """Stores the score (and optionally the report text) on a holder.

        Args:
            holder (str): Holder from find_score_holder.
            score_attribute (str): Integer attribute or property name.
            score (int): Score 0-100.
            report_attribute (str, optional): String attribute name; empty skips the report.
            report_text (str, optional): Compact report JSON.

        Raises:
            ValueError: If the attributes cannot be written.
        """
        raise NotImplementedError(f"{self.label} cannot store scores in the scene.")

    # ------------------------------------------------ Optional Dependencies ------------------------------------
    def get_python_executable(self):
        """Gets the Python executable that runs this host's scripts (used for pip installs).

        Returns:
            str: Python executable path.
        """
        return sys.executable

    def get_dependency_target(self):
        """Gets the folder where pip should install optional packages for this host.

        Returns:
            str: Folder on this host's sys.path, or "" to let pip use its default location.
        """
        return ""

    def build_pip_install_command(self, packages):
        """Builds the pip command that installs optional packages (for example Qt for graphs).

        Args:
            packages (list): Package names.

        Returns:
            list: Command arguments.
        """
        command = [self.get_python_executable(), "-m", "pip", "install", "--disable-pip-version-check"]
        target = self.get_dependency_target()
        command += ["--target", target] if target else ["--user"]
        return command + list(packages)
