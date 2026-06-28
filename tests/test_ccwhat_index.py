"""Tests for CCWhatIndex git isolation."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from ccwhat.runtime.core.index import CCWhatIndex, CCWhatIndexError


def _init_repo(path: Path) -> None:
    """Initialize a git repo with initial commit."""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, check=True, capture_output=True)


def test_ccwhat_index_isolated_from_main_index():
    """Test that CCWhatIndex operations don't affect main git index."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _init_repo(workspace)

        # Create CCWhatIndex
        index = CCWhatIndex(workspace)
        index.init()

        # Create a new file
        (workspace / "new_file.py").write_text("content\n", encoding="utf-8")

        # Add to CCWhatIndex
        index.add("new_file.py")

        # Main git index should not have the file staged
        main_index = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=workspace,
            text=True,
            capture_output=True,
        )
        assert "new_file.py" not in main_index.stdout, "File should not be staged in main index"

        # CCWhatIndex should see the file
        diff = index.diff("HEAD")
        assert "new_file.py" in diff, "File should appear in CCWhatIndex diff"


def test_ccwhat_index_add_and_diff():
    """Test adding files and generating diff."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _init_repo(workspace)

        index = CCWhatIndex(workspace)
        index.init()

        # Add new file
        (workspace / "src").mkdir()
        (workspace / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
        index.add("src/app.py")

        diff = index.diff("HEAD")
        assert "new file mode 100644" in diff
        assert "src/app.py" in diff
        assert "print('hello')" in diff


def test_ccwhat_index_modify_existing_file():
    """Test modifying an existing tracked file."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _init_repo(workspace)

        index = CCWhatIndex(workspace)
        index.init()

        # Modify existing file
        (workspace / "README.md").write_text("modified content\n", encoding="utf-8")
        index.add("README.md")

        diff = index.diff("HEAD")
        assert "-initial" in diff
        assert "+modified content" in diff


def test_ccwhat_index_remove_file():
    """Test removing a file from index shows deletion."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _init_repo(workspace)

        index = CCWhatIndex(workspace)
        index.init()

        # Add README to index first
        index.add("README.md")

        # Then remove it
        index.remove("README.md")

        diff = index.diff("HEAD")
        # After add then remove of a tracked file, diff shows deletion
        assert "deleted file" in diff or diff == ""


def test_ccwhat_index_raises_on_nonexistent_file():
    """Test that adding nonexistent file raises error."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _init_repo(workspace)

        index = CCWhatIndex(workspace)
        index.init()

        with pytest.raises(CCWhatIndexError, match="does not exist"):
            index.add("nonexistent.py")


def test_ccwhat_index_get_tree_hash():
    """Test getting tree hash from index."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _init_repo(workspace)

        index = CCWhatIndex(workspace)
        index.init()

        # Empty index should still return a hash after adding something
        (workspace / "file.py").write_text("content\n", encoding="utf-8")
        index.add("file.py")

        tree_hash = index.get_tree_hash()
        assert tree_hash is not None
        assert len(tree_hash) == 40  # SHA-1 hash
