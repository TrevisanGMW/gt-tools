"""
Repair scene access: resolves nodes (by role or name), samples world matrices, and keys local
transforms through the active host. Fixes only talk to the scene through this class.
"""

from .. import math_utils
from .. import sampling
from .. import templates
from . import transform_math

ROLE_SUFFIX_SEPARATOR = " ("


def clean_node_label(label):
    """Turns a report offender label such as ``"foot_l (left_foot)"`` into a node name.

    Args:
        label (str): Node name, long path, or report label.

    Returns:
        str: Node name or path without the role suffix.
    """
    text = str(label or "").strip()
    if text.endswith(")") and ROLE_SUFFIX_SEPARATOR in text:
        text = text[:text.rindex(ROLE_SUFFIX_SEPARATOR)]
    return text.strip()


class RepairScene:
    """Scene access shared by every fix of one patch."""

    def __init__(self, host=None, template=None):
        """Initializes the scene access.

        Args:
            host (SceneHost, optional): Host to use. Defaults to the active host.
            template (dict, optional): Skeleton template used to resolve roles.
        """
        self.host = host or sampling.get_host()
        self.template = templates.normalize_template(template) if template else None
        self._roles = None
        self._node_paths = None
        self.warnings = []

    @property
    def node_paths(self):
        """Gets every joint and transform path in the scene (listed once).

        Returns:
            list: Node paths.
        """
        if self._node_paths is None:
            self._node_paths = list(self.host.list_joints()) + list(self.host.list_transforms())
        return self._node_paths

    @property
    def roles(self):
        """Gets the resolved role paths (resolved once).

        Returns:
            dict: Role key to node path.
        """
        if self._roles is None:
            self._roles = {}
            if self.template:
                resolution = templates.resolve_template_roles(self.template, self.node_paths,
                                                              required_roles=[])
                self._roles = dict(resolution.get("roles") or {})
                self.warnings.extend(resolution.get("warnings") or [])
        return self._roles

    def get_up_axis(self):
        """Gets the up axis.

        Returns:
            str: "y" or "z".
        """
        template_axis = str((self.template or {}).get("up_axis") or "scene").lower()
        if template_axis in ("y", "z"):
            return template_axis
        return str(self.host.get_up_axis() or "y").lower()

    def resolve_node(self, name_or_role):
        """Resolves a role key, node name, report label, or path to one node path.

        Args:
            name_or_role (str): Role key (for example "left_foot"), name, or path.

        Returns:
            str: Node path.

        Raises:
            ValueError: When nothing or more than one node matches.
        """
        text = clean_node_label(name_or_role)
        role_text = text.lower().replace(" ", "_")
        if role_text in templates.ROLE_KEYS and text not in templates.ROLE_KEYS:
            text = role_text
        if text in templates.ROLE_KEYS:
            if text not in self.roles:
                raise ValueError(f'Role "{text}" is not resolved; give the patch a skeleton template or a node name.')
            return self.roles[text]
        if text.startswith("|"):
            matches = [path for path in self.node_paths if path == text]
        else:
            short_name = text.split("|")[-1]
            matches = [path for path in self.node_paths
                       if templates.split_node_name(path)[1] == short_name.split(":")[-1]
                       and (":" not in short_name or path.split("|")[-1] == short_name)]
        if len(matches) != 1:
            found = "nothing" if not matches else f"{len(matches)} nodes"
            raise ValueError(f'Node "{text}" matched {found}; use a long path or a namespaced name.')
        return matches[0]

    def get_parent(self, node_path):
        """Gets a node's parent path.

        Args:
            node_path (str): Node path.

        Returns:
            str or None: Parent path.
        """
        return self.host.get_parents([node_path]).get(node_path)

    def sample(self, node_paths, start_frame, end_frame):
        """Samples world matrices, including each node's parent.

        Args:
            node_paths (list): Node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame.

        Returns:
            tuple: (matrices by path, parents by path).
        """
        parents = self.host.get_parents(list(node_paths))
        to_sample = list(node_paths) + [parent for parent in parents.values() if parent and parent not in node_paths]
        matrices = self.host.sample_world_matrices(to_sample, int(start_frame), int(end_frame))
        return matrices, parents

    def key_world_matrices(self, node_path, frames, world_matrices, parent_world_matrices, channels):
        """Keys a node so it reaches the given world matrices.

        Args:
            node_path (str): Node path.
            frames (list): Frame numbers.
            world_matrices (list): Target world matrices.
            parent_world_matrices (list): Parent world matrices for the same frames (None entries
                for a top node).
            channels (tuple): "rotate" and/or "translate".

        Returns:
            dict: {"keys": int, "warnings": list}.
        """
        local_matrices = [transform_math.local_from_world(world, parent)
                          for world, parent in zip(world_matrices, parent_world_matrices)]
        return self.host.key_local_transforms(node_path, list(frames), local_matrices, tuple(channels))

    def get_positions(self, matrices):
        """Gets the positions of a matrix list.

        Args:
            matrices (list): World matrices.

        Returns:
            list: Positions.
        """
        return [math_utils.matrix_position(matrix) for matrix in matrices]
