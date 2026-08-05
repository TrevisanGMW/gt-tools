"""
Undo Utilities

Import Line:
    import gt.core.undo as core_undo
"""

import maya.cmds as cmds
import functools
import traceback
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UndoChunk:
    """Context manager to group Maya commands into a single undoable action."""

    def __init__(self, chunk_name=""):
        """
        Initialize an undo chunk context manager.

        Args:
            chunk_name (str, optional): Name for the undo chunk. Defaults to "".
        """
        self._chunk_name = chunk_name

    def __enter__(self):
        """
        Open the undo chunk when entering the context.

        Returns:
            UndoChunk: The instance of this context manager.
        """
        cmds.undoInfo(openChunk=True, undoName=self._chunk_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the undo chunk when exiting the context.

        If an exception occurred within the context, the undo chunk is rolled back.

        Args:
            exc_type (type): Exception type if raised, else None.
            exc_val (Exception): Exception value if raised, else None.
            exc_tb (traceback): Traceback object if raised, else None.

        Returns:
            bool: False to propagate exceptions, True to suppress them.
        """
        try:
            cmds.undoInfo(closeChunk=True)
        except Exception:
            cmds.warning(f"Failed to close undo chunk:\n{traceback.format_exc()}")

        # Roll back the chunk if there was an exception
        if exc_type:
            try:
                cmds.undo()
            except Exception:
                cmds.warning(f"Undo failed:\n{traceback.format_exc()}")

        # Propagate exception (if any)
        return False


class UndoSuspended:
    """Context manager to temporarily suspend Maya's undo system."""

    def __enter__(self):
        """
        Disable Maya's undo system upon entering the context.

        Returns:
            UndoSuspended: The instance of this context manager.
        """
        self._previous_state = cmds.undoInfo(q=True, stateWithoutFlush=True)
        cmds.undoInfo(stateWithoutFlush=False)  # Disable undo
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Restore Maya's undo system to its previous state upon exiting the context.

        Args:
            exc_type (type): Exception type if raised, else None.
            exc_val (Exception): Exception value if raised, else None.
            exc_tb (traceback): Traceback object if raised, else None.
        """
        cmds.undoInfo(stateWithoutFlush=self._previous_state)  # Restore state


def suspend_undo(func):
    """Decorator to disable Maya's undo system while executing a function.

    Args:
        func (Callable): Function to wrap.

    Returns:
        Callable: Wrapped function with undo temporarily disabled.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function that disables undo, executes the original function,
        and restores undo state afterward.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            Any: The result returned by the wrapped function.
        """
        previous_state = cmds.undoInfo(q=True, stateWithoutFlush=True)
        try:
            cmds.undoInfo(stateWithoutFlush=False)  # Disable undo
            return func(*args, **kwargs)
        finally:
            cmds.undoInfo(stateWithoutFlush=previous_state)  # Restore state

    return wrapper


def undo_chunk(func=None, *, chunk_name=""):
    """Decorator to wrap a function's operations inside a single undo chunk.

    This groups all commands inside the function into one undo step.
    If an exception is raised, the undo chunk will be rolled back.

    Args:
        func (Callable, optional): Function to wrap. Defaults to None.
        chunk_name (str, optional): Name for the undo chunk. Defaults to "".

    Returns:
        Callable: Wrapped function with operations grouped in one undo step.
    """

    def decorator(fn):
        """
        Inner decorator that wraps the given function inside a Maya undo chunk.

        Args:
            fn (Callable): Function whose operations should be grouped in one undo chunk.

        Returns:
            Callable: Wrapped function that runs inside an undo chunk.
        """

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that disables undo, executes the original function,
            and restores undo state afterward.

            Args:
                *args: Positional arguments for the wrapped function.
                **kwargs: Keyword arguments for the wrapped function.

            Returns:
                Any: The result returned by the wrapped function.
            """
            cmds.undoInfo(openChunk=True, undoName=chunk_name)
            try:
                return fn(*args, **kwargs)
            except Exception:
                # Roll back if the function raises an error
                try:
                    cmds.undo()
                except Exception:
                    cmds.warning(f"Undo failed:\n{traceback.format_exc()}")
                raise
            finally:
                try:
                    cmds.undoInfo(closeChunk=True)
                except Exception:
                    cmds.warning(f"Failed to close undo chunk:\n{traceback.format_exc()}")

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
