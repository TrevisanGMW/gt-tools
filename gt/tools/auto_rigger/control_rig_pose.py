"""
Auto Rigger Control Rig Pose Data

Pure data helpers used to serialize and validate custom control rig poses.
"""

import copy
import hashlib
import json
import math


class ControlRigPoseMode:
    """Constants describing how a project determines its control rig pose."""

    AUTOMATIC = "automatic"
    CUSTOM = "custom"
    DISABLED = "disabled"

    @classmethod
    def get_modes(cls):
        """Gets all supported control rig pose modes.

        Returns:
            list: Supported control rig pose mode strings.
        """
        return [cls.AUTOMATIC, cls.CUSTOM, cls.DISABLED]

    @classmethod
    def is_valid(cls, mode):
        """Checks whether a value is a supported control rig pose mode.

        Args:
            mode (str): Mode value to validate.

        Returns:
            bool: True when the mode is supported.
        """
        return isinstance(mode, str) and mode in cls.get_modes()


def build_data_signature(data):
    """Builds a stable SHA-256 signature for JSON-compatible data.

    Args:
        data (any): JSON-compatible data used to build the signature.

    Returns:
        str: Hexadecimal SHA-256 signature.
    """
    serialized_data = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()


def get_proxy_signature_data(project_data):
    """Extracts skeleton-relevant module data from a serialized rig project.

    Args:
        project_data (dict): Serialized rig project data.

    Returns:
        list: Active module and proxy data used to detect stale pose captures.
    """
    if not isinstance(project_data, dict):
        return []
    signature_data = []
    for module_data in project_data.get("modules") or []:
        if not isinstance(module_data, dict):
            continue
        if module_data.get("active", True) is False or not module_data.get("proxies"):
            continue
        signature_data.append(
            {
                "module": module_data.get("module"),
                "uuid": module_data.get("uuid"),
                "parent": module_data.get("parent"),
                "orientation": module_data.get("orientation"),
                "proxies": copy.deepcopy(module_data.get("proxies", {})),
            }
        )
    return signature_data


def build_proxy_signature(project_data):
    """Builds a stable signature for a serialized rig project's proxy configuration.

    Args:
        project_data (dict): Serialized rig project data.

    Returns:
        str: SHA-256 signature for active module and proxy data.
    """
    return build_data_signature(get_proxy_signature_data(project_data))


def is_matrix_valid(matrix):
    """Checks whether a value is a valid serialized four-by-four matrix.

    Args:
        matrix (list, tuple): Matrix components to validate.

    Returns:
        bool: True when the value contains sixteen numeric components.
    """
    if not isinstance(matrix, (list, tuple)) or len(matrix) != 16:
        return False
    return all(
        isinstance(component, (int, float)) and not isinstance(component, bool) and math.isfinite(component)
        for component in matrix
    )


class ControlRigPoseData:
    """Stores a versioned custom control rig pose keyed by proxy UUID."""

    SCHEMA_VERSION = 1

    def __init__(self, project_uuid=None, proxy_signature=None, transforms=None):
        """Initializes a control rig pose data object.

        Args:
            project_uuid (str, optional): UUID of the project used to capture the pose.
            proxy_signature (str, optional): Signature of the proxy configuration used for capture.
            transforms (dict, optional): Mapping of proxy UUIDs to serialized matrix data.
        """
        self.schema_version = self.SCHEMA_VERSION
        self.project_uuid = None
        self.proxy_signature = None
        self.transforms = {}

        if project_uuid:
            self.set_project_uuid(project_uuid)
        if proxy_signature:
            self.set_proxy_signature(proxy_signature)
        if transforms:
            self.set_transforms(transforms)

    def set_project_uuid(self, project_uuid):
        """Sets the project UUID associated with the captured pose.

        Args:
            project_uuid (str, None): Project UUID or None to clear it.

        Returns:
            bool: True when the value was accepted.
        """
        if project_uuid is not None and not isinstance(project_uuid, str):
            return False
        self.project_uuid = project_uuid
        return True

    def set_proxy_signature(self, proxy_signature):
        """Sets the signature of the proxy configuration used for capture.

        Args:
            proxy_signature (str, None): Proxy signature or None to clear it.

        Returns:
            bool: True when the value was accepted.
        """
        if proxy_signature is not None and not isinstance(proxy_signature, str):
            return False
        self.proxy_signature = proxy_signature
        return True

    def set_transforms(self, transforms):
        """Sets serialized joint transforms keyed by proxy UUID.

        Args:
            transforms (dict): Mapping of proxy UUIDs to dictionaries containing a matrix.

        Returns:
            bool: True when the mapping was accepted.
        """
        if not isinstance(transforms, dict):
            return False
        self.transforms = copy.deepcopy(transforms)
        return True

    def clear(self):
        """Clears all captured custom pose data."""
        self.schema_version = self.SCHEMA_VERSION
        self.project_uuid = None
        self.proxy_signature = None
        self.transforms = {}

    def has_pose(self):
        """Checks whether any custom transform data is stored.

        Returns:
            bool: True when at least one transform is stored.
        """
        return bool(self.transforms)

    def get_transform_count(self):
        """Gets the number of stored proxy transforms.

        Returns:
            int: Number of stored proxy transforms.
        """
        return len(self.transforms)

    def get_data_as_dict(self):
        """Serializes the custom pose into JSON-compatible data.

        Returns:
            dict: Serialized control rig pose data.
        """
        return {
            "schema_version": self.schema_version,
            "project_uuid": self.project_uuid,
            "proxy_signature": self.proxy_signature,
            "transforms": copy.deepcopy(self.transforms),
        }

    def read_data_from_dict(self, data):
        """Reads serialized custom pose data.

        Args:
            data (dict): Serialized control rig pose data.

        Returns:
            ControlRigPoseData: This object.
        """
        self.clear()
        if not isinstance(data, dict):
            return self

        schema_version = data.get("schema_version", self.SCHEMA_VERSION)
        if isinstance(schema_version, int):
            self.schema_version = schema_version
        self.set_project_uuid(data.get("project_uuid"))
        self.set_proxy_signature(data.get("proxy_signature"))
        self.set_transforms(data.get("transforms", {}))
        return self

    def validate(self, project_uuid=None, proxy_signature=None, expected_proxy_uuids=None):
        """Validates stored pose data against an optional project configuration.

        Args:
            project_uuid (str, optional): UUID of the project receiving the pose.
            proxy_signature (str, optional): Current signature of the project proxy configuration.
            expected_proxy_uuids (list, set, tuple, optional): Proxy UUIDs expected to have stored transforms.

        Returns:
            dict: Validation result containing valid, errors, warnings, and transform_count keys.
        """
        errors = []
        warnings = []

        if self.schema_version != self.SCHEMA_VERSION:
            errors.append(
                f"Unsupported control pose schema version: {self.schema_version}. "
                f"Expected: {self.SCHEMA_VERSION}."
            )
        if not self.transforms:
            errors.append("No custom control pose transforms are stored.")
        if not self.project_uuid:
            errors.append("The custom control pose is missing its source project UUID.")
        if not self.proxy_signature:
            errors.append("The custom control pose is missing its proxy configuration signature.")
        if project_uuid and self.project_uuid and project_uuid != self.project_uuid:
            errors.append("The custom control pose was captured from a different rig project.")
        if proxy_signature and self.proxy_signature and proxy_signature != self.proxy_signature:
            errors.append("The project proxy configuration changed after the custom control pose was captured.")

        invalid_proxy_uuids = []
        for proxy_uuid, transform_data in self.transforms.items():
            matrix = transform_data.get("matrix") if isinstance(transform_data, dict) else None
            if not isinstance(proxy_uuid, str) or not is_matrix_valid(matrix):
                invalid_proxy_uuids.append(str(proxy_uuid))
        if invalid_proxy_uuids:
            errors.append(f"Invalid matrices were found for proxy UUIDs: {', '.join(invalid_proxy_uuids)}")

        expected_proxy_uuids = set(expected_proxy_uuids or [])
        stored_proxy_uuids = set(self.transforms.keys())
        missing_proxy_uuids = sorted(expected_proxy_uuids - stored_proxy_uuids)
        extra_proxy_uuids = sorted(stored_proxy_uuids - expected_proxy_uuids) if expected_proxy_uuids else []
        if missing_proxy_uuids:
            errors.append(f"The custom control pose is missing {len(missing_proxy_uuids)} proxy transform(s).")
        if extra_proxy_uuids:
            warnings.append(f"The custom control pose contains {len(extra_proxy_uuids)} unused proxy transform(s).")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "transform_count": len(self.transforms),
        }
