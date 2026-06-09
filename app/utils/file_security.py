"""File security utilities — prevent path traversal outside white-listed directories."""

import os


def resolve_path_within_directory(base_dir: str, unsafe_path: str) -> str:
    """Resolve `unsafe_path` relative to `base_dir` and ensure it stays within bounds.

    Raises:
        ValueError: If the resolved path escapes `base_dir` or the file does not exist.
    """
    # Normalize the base directory
    base_dir = os.path.realpath(os.path.normpath(base_dir))

    # If unsafe_path is already absolute, try to use it directly
    if os.path.isabs(unsafe_path):
        resolved = os.path.realpath(os.path.normpath(unsafe_path))
    else:
        resolved = os.path.realpath(os.path.normpath(os.path.join(base_dir, unsafe_path)))

    # Check that the resolved path starts with the base directory
    if not resolved.startswith(base_dir + os.sep) and resolved != base_dir:
        raise ValueError(
            f"path traversal detected: {unsafe_path} resolves to {resolved}, "
            f"which is outside {base_dir}"
        )

    if not os.path.exists(resolved):
        raise ValueError(f"file does not exist: {resolved}")

    return resolved
