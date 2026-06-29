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
        """Initialize index from HEAD.

        Creates a git index starting from HEAD commit's tree. This ensures
        we can track deletions by comparing the current index state with
        the actual filesystem at finish time.
        """
        # Start from HEAD to track all files, not just modified ones
        self._git_cmd(["read-tree", "HEAD"])

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

    def sync_workspace(self) -> None:
        """Stage all working-tree changes into the isolated index.

        Captures any file change that bypassed the Write/Edit hooks (mv, sed,
        echo redirection, cp, ...). Uses ``git add -A`` with the isolated
        GIT_INDEX_FILE so the user's real index is never touched.
        """
        self._git_cmd(["add", "-A"])

    def diff(self, base_commit: str = "HEAD") -> str:
        """Generate diff between base_commit and current index.

        Uses --cached to compare the staged index against base_commit,
        ensuring we see changes tracked in our isolated index.

        Args:
            base_commit: Commit to diff against (default: HEAD)

        Returns:
            Unified diff as string
        """
        result = subprocess.run(
            ["git", "diff", "--cached", "--binary", base_commit],
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

    def reconcile_deletions(self) -> list[str]:
        """Remove files from index that no longer exist on disk.

        This detects file deletions (e.g., via Bash rm) that weren't
        captured by the Write/Edit/MultiEdit hooks.

        Returns:
            List of deleted file paths
        """
        # Get all files currently in our index
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=self.workspace,
            env=self._env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            return []

        deleted: list[str] = []
        for tracked in result.stdout.splitlines():
            if tracked and not (self.workspace / tracked).exists():
                # File was deleted from disk, remove from index
                self._git_cmd(["rm", "--cached", tracked], check=False)
                deleted.append(tracked)

        return deleted

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

    def write_tree(self) -> str | None:
        """Write the isolated index to a tree object and return its hash."""
        return self.get_tree_hash()

    def diff_working(self, prev_tree: str | None) -> str:
        """Diff the working tree against *prev_tree* (or HEAD if None).

        Unlike :meth:`diff` (which compares the staged index), this compares
        the actual working tree, so it reflects on-disk changes from any
        source (Write/Edit/Bash mv/sed/...). The isolated GIT_INDEX_FILE is
        still set so git does not touch the user's real index.
        """
        ref = prev_tree or "HEAD"
        result = subprocess.run(
            ["git", "diff", "--binary", ref],
            cwd=self.workspace,
            env=self._env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout

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
