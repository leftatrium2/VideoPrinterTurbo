"""Publish a complete result atomically without replacing an existing file."""
import ctypes
import errno
import os
import sys


def _rename_noreplace(source, target):
    if sys.platform == 'win32':
        # Windows os.rename fails if the target exists, including on exFAT/SMB.
        os.rename(source, target)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith('linux') and hasattr(libc, 'renameat2'):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(-100, os.fsencode(source), -100, os.fsencode(target), 1)  # RENAME_NOREPLACE
    elif sys.platform == 'darwin' and hasattr(libc, 'renamex_np'):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(os.fsencode(source), os.fsencode(target), 4)  # RENAME_EXCL
    else:
        raise OSError(errno.ENOTSUP, 'Filesystem requires atomic exclusive rename support', str(target))
    if result != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(target))


def publish_result(part, output):
    try:
        os.link(part, output)
    except OSError as exc:
        unsupported = exc.errno in {errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}
        unsupported = unsupported or getattr(exc, 'winerror', None) in {1, 50}
        if not unsupported:
            raise
        # No copy-to-final fallback: that would expose an incomplete output.
        _rename_noreplace(part, output)
