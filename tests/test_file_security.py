import os
import pytest
from app.utils.file_security import resolve_path_within_directory


def test_valid_relative_path(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    result = resolve_path_within_directory(str(tmp_path), "data.txt")
    assert result == str(f.resolve())


def test_valid_absolute_path_inside_base(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    result = resolve_path_within_directory(str(tmp_path), str(f))
    assert result == str(f.resolve())


def test_relative_path_traversal_raises(tmp_path):
    with pytest.raises(ValueError, match="path traversal"):
        resolve_path_within_directory(str(tmp_path), "../../etc/passwd")


def test_absolute_path_outside_base_raises(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret")
    with pytest.raises(ValueError, match="path traversal"):
        resolve_path_within_directory(str(tmp_path), str(outside))


def test_nonexistent_file_raises(tmp_path):
    with pytest.raises(ValueError, match="file does not exist"):
        resolve_path_within_directory(str(tmp_path), "missing.txt")


def test_path_pointing_to_base_dir_itself(tmp_path):
    result = resolve_path_within_directory(str(tmp_path), str(tmp_path))
    assert result == str(tmp_path.resolve())
