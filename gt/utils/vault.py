"""Stores secrets such as API keys encrypted for the current Windows user.

Encryption uses the Windows Data Protection API (DPAPI) through ``ctypes``. Data is bound to the **current user
account** (the ``CRYPTPROTECT_LOCAL_MACHINE`` flag is deliberately never used), so other Windows users on the same
computer cannot decrypt it, and neither can the same user on another computer. No password prompt is ever shown,
which keeps the module usable in unattended Maya batch processes.

This module is pure Python and importable outside Maya. It never logs or returns secrets in error messages.

Example:
    >>> from gt.utils import vault
    >>> vault.store_secret("vlm_openai", "sk-...", directory)
    >>> vault.load_secret("vlm_openai", directory)
"""

import base64
import ctypes
import json
import os
import re
import sys
import tempfile
from pathlib import Path

FILE_SUFFIX = ".secret"
FILE_VERSION = 1
SCHEME = "dpapi-current-user"
DEFAULT_ENTROPY = b"gt-tools.vault.v1"
CRYPTPROTECT_UI_FORBIDDEN = 0x1
_NAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{1,80}")


class VaultError(RuntimeError):
    """Raised when a secret cannot be protected, stored, or read."""


def is_supported():
    """Checks whether current-user encryption is available on this platform.

    Returns:
        bool: True on Windows.
    """
    return sys.platform == "win32"


def get_default_directory():
    """Resolves the default folder for secret files next to the GT-Tools preferences.

    Returns:
        Path: Folder that holds ``.secret`` files. It is not created here.
    """
    try:
        from gt.core.prefs import get_prefs_dir
    except ModuleNotFoundError as error:
        if error.name not in ("maya", "maya.cmds"):
            raise
        from gt.utils.system import get_maya_preferences_dir, get_system

        return Path(get_maya_preferences_dir(get_system())) / "gt-tools" / "prefs" / "secrets"
    return Path(get_prefs_dir()) / "secrets"


def _blob_type():
    """Creates the Windows DATA_BLOB structure type.

    Returns:
        type: ctypes structure with a size and a data pointer.
    """
    from ctypes import wintypes

    class DataBlob(ctypes.Structure):
        """Windows DATA_BLOB."""

        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    return DataBlob


def _transform(data, entropy, protect):
    """Runs CryptProtectData or CryptUnprotectData with the current-user scope.

    Args:
        data (bytes): Plain bytes to protect, or protected bytes to read.
        entropy (bytes): Extra application-specific bytes that must match when unprotecting.
        protect (bool): True to encrypt, False to decrypt.

    Returns:
        bytes: Transformed bytes.
    """
    if not is_supported():
        raise VaultError("Current-user encryption is only available on Windows.")
    from ctypes import wintypes

    blob_type = _blob_type()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    function = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    function.restype = wintypes.BOOL

    def make_blob(content):
        """Wraps bytes in a DATA_BLOB and keeps the buffer alive.

        Args:
            content (bytes): Bytes to wrap.

        Returns:
            tuple: DATA_BLOB and its backing buffer.
        """
        buffer = ctypes.create_string_buffer(content, len(content))
        return blob_type(len(content), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer

    source, source_buffer = make_blob(data)
    extra, extra_buffer = make_blob(entropy) if entropy else (None, None)
    result = blob_type()
    description = ctypes.c_wchar_p("gt-tools secret") if protect else None
    arguments = [ctypes.byref(source)]
    arguments += [description] if protect else [None]
    arguments += [ctypes.byref(extra) if extra is not None else None, None, None, CRYPTPROTECT_UI_FORBIDDEN]
    arguments.append(ctypes.byref(result))
    # Current user scope: CRYPTPROTECT_LOCAL_MACHINE is intentionally not set.
    if not function(*arguments):
        raise VaultError(f"Windows could not {'protect' if protect else 'unprotect'} the data.")
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        kernel32.LocalFree(result.pbData)
        del source_buffer, extra_buffer


def protect_text(text, entropy=DEFAULT_ENTROPY):
    """Encrypts text for the current Windows user.

    Args:
        text (str): Secret to encrypt. It must not be empty.
        entropy (bytes, optional): Application-specific bytes required again to decrypt.

    Returns:
        str: Base64 text safe to store in a file.
    """
    if not isinstance(text, str) or not text:
        raise VaultError("Enter a non-empty secret to protect.")
    return base64.b64encode(_transform(text.encode("utf-8"), entropy, True)).decode("ascii")


def unprotect_text(token, entropy=DEFAULT_ENTROPY):
    """Decrypts text that was encrypted by the same Windows user.

    Args:
        token (str): Base64 text returned by protect_text.
        entropy (bytes, optional): Same bytes that were used to encrypt.

    Returns:
        str: Original secret.
    """
    try:
        data = base64.b64decode(token.encode("ascii"), validate=True)
    except (ValueError, AttributeError) as error:
        raise VaultError("The stored secret is not valid.") from error
    try:
        return _transform(data, entropy, False).decode("utf-8")
    except UnicodeDecodeError as error:
        raise VaultError("The stored secret is not valid.") from error


def _secret_path(name, directory):
    """Builds the file path for a named secret.

    Args:
        name (str): Secret name made of letters, digits, underscore, dot, or dash.
        directory (str or Path or None): Folder for secret files, or None for the default.

    Returns:
        Path: Secret file path.
    """
    if not isinstance(name, str) or not _NAME_PATTERN.fullmatch(name):
        raise VaultError("Secret names may only use letters, numbers, underscore, dot, and dash.")
    folder = Path(directory) if directory else get_default_directory()
    return folder / f"{name}{FILE_SUFFIX}"


def store_secret(name, value, directory=None, entropy=DEFAULT_ENTROPY):
    """Encrypts and saves a named secret, replacing any previous value.

    Args:
        name (str): Secret name, for example ``vlm_openai``.
        value (str): Secret value.
        directory (str or Path, optional): Folder for secret files. Defaults to the GT-Tools prefs secrets folder.
        entropy (bytes, optional): Application-specific bytes required again to decrypt.

    Returns:
        Path: Saved file.
    """
    path = _secret_path(name, directory)
    document = {"version": FILE_VERSION, "scheme": SCHEME, "data": protect_text(value, entropy)}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, mode="w", encoding="utf-8", suffix=".tmp", delete=False
        ) as stream:
            temporary_path = Path(stream.name)
            json.dump(document, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return path


def load_secret(name, directory=None, entropy=DEFAULT_ENTROPY):
    """Reads and decrypts a named secret.

    Args:
        name (str): Secret name.
        directory (str or Path, optional): Folder for secret files.
        entropy (bytes, optional): Same bytes that were used to store it.

    Returns:
        str: Secret value, or an empty string when none is stored.
    """
    path = _secret_path(name, directory)
    if not path.is_file():
        return ""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise VaultError(f"Could not read the stored secret '{name}'.") from error
    if not isinstance(document, dict) or document.get("scheme") != SCHEME or not isinstance(document.get("data"), str):
        raise VaultError(f"The stored secret '{name}' uses an unsupported format.")
    return unprotect_text(document["data"], entropy)


def has_secret(name, directory=None):
    """Checks whether a secret file exists without decrypting it.

    Args:
        name (str): Secret name.
        directory (str or Path, optional): Folder for secret files.

    Returns:
        bool: True when a secret file is present.
    """
    return _secret_path(name, directory).is_file()


def delete_secret(name, directory=None):
    """Deletes a stored secret file.

    Args:
        name (str): Secret name.
        directory (str or Path, optional): Folder for secret files.

    Returns:
        bool: True when a file was removed.
    """
    path = _secret_path(name, directory)
    if not path.is_file():
        return False
    path.unlink()
    return True
