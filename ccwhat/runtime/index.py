"""GIT_INDEX_FILE based isolated git index for incremental diff tracking."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


class CCWhatIndexError(RuntimeError):
    """Error related to CCWhatIndex operations."""

    pass


class CCWhatIndex:
    """Isolated git index using GIT_INDEX_FILE.

    This class provides a staging area that is completely separate from the
    main git index, allowing us to track file changes without polluting the
    user's working directory.
    """

    def __init__(self, workspace: Path, index_path: str = ".git/index.ccwhat") -> None:
        """Initialize CCWhatIndex.

        Args:
            workspace: Path to the git workspace
            index_path: Relative path to the isolated index file
        """
        self.workspace = Path(workspace)
        self.index_path = self.workspace / index_path
        self._env = {**os.environ, "GIT_INDEX_FILE": str(self.index_path)}

    def init(self) -> None:
        """Initialize an empty index.

        Creates an empty git index file. If the index already exists,
        it will be cleared.
        """
        # Create empty index by reading from an empty tree
        self._git_cmd(["read-tree", "--empty"])

    def add(self, file_path: str | Path) -> None:
        """Add a file to the isolated index.

        Args:
            file_path: Path to the file (relative to workspace)

        Raises:
            CCWhatIndexError: If the file doesn't exist or git add fails
        """
        rel_path = Path(file_path)
        full_path = self.workspace / rel_path
        if not full_path.exists():
            raise CCWhatIndexError(f"File does not exist: {full_path}")

        self._git_cmd(["add", str(rel_path)])

    def remove(self, file_path: str | Path) -> None:
        """Remove a file from the isolated index.

        Args:
            file_path: Path to the file (relative to workspace)
        """
        rel_path = Path(file_path)
        self._git_cmd(["rm", "--cached", str(rel_path)], check=False)

    def diff(self, base_commit: str = "HEAD") -> str:
        """Generate diff between base_commit and current index.

        Args:
            base_commit: Commit to diff against (default: HEAD)

        Returns:
            Unified diff as string
        """
        result = subprocess.run(
            ["git", "diff", "--binary", base_commit],
            cwd=self.workspace,
            env=self._env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout

    def diff_step(self, prev_ref: str) -> str:
        """Generate diff between prev_ref and current index.

        This is useful for generating incremental diffs between steps.

        Args:
            prev_ref: Previous reference (commit, tree, etc.)

        Returns:
            Unified diff as string
        """
        return self.diff(prev_ref)

    def get_tree_hash(self) -> str | None:
        """Get the current tree hash of the index.

        Returns:
            Tree hash or None if index is empty
        """
        result = subprocess.run(
            ["git", "write-tree"],
            cwd=self.workspace,
            env=self._env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def _git_cmd(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[Any]:
        """Run a git command with the isolated index.

        Args:
            args: Git command arguments
            check: Whether to check return code

        Returns:
            CompletedProcess instance
        """
        result = subprocess.run(
            ["git", *args],
            cwd=self.workspace,
            env=self._env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if check and result.returncode != 0:
            raise CCWhatIndexError(f"Git command failed: {result.stderr}")
        return result
