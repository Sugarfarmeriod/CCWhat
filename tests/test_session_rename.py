"""Tests for session rename: adapter rename, viewer API, and frontend elements."""

from __future__ import annotations

import json
import sqlite3
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ccwhat.adapters.base import AgentAdapter, SessionRenameError
from ccwhat.adapters.claude import ClaudeAdapter
from ccwhat.adapters.codex import CodexAdapter
from ccwhat.adapters.opencode import OpenCodeAdapter


# ---------------------------------------------------------------------------
# 6.1 Adapter interface tests: title/displayName/canRenameSession
# ---------------------------------------------------------------------------


class TestAdapterTitleMetadata(unittest.TestCase):
    """Verify adapters return title, displayName, canRenameSession in session data."""

    def test_claude_adapter_can_rename_is_false(self):
        adapter = ClaudeAdapter(Path("/nonexistent"))
        self.assertFalse(adapter.can_rename_session)

    def test_codex_adapter_can_rename_is_true(self):
        adapter = CodexAdapter(Path("/nonexistent"))
        self.assertTrue(adapter.can_rename_session)

    def test_opencode_adapter_can_rename_is_true(self):
        adapter = OpenCodeAdapter(Path("/nonexistent"))
        self.assertTrue(adapter.can_rename_session)

    def test_claude_rename_raises_unsupported(self):
        adapter = ClaudeAdapter(Path("/nonexistent"))
        with self.assertRaises(SessionRenameError) as ctx:
            adapter.rename_session("some-id", "New Title")
        self.assertEqual(ctx.exception.code, "rename_not_supported")

    def test_claude_list_projects_includes_title_fields(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            proj = pd / "my-project"
            proj.mkdir()
            sid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            (proj / f"{sid}.jsonl").write_text(
                json.dumps({"type": "user", "content": "hi", "timestamp": "2025-01-01T00:00:00Z"}) + "\n"
            )
            adapter = ClaudeAdapter(pd)
            projects = adapter.list_projects()
            self.assertEqual(len(projects), 1)
            sess = projects[0]["sessions"][0]
            self.assertIn("title", sess)
            self.assertIn("displayName", sess)
            self.assertIn("canRenameSession", sess)
            self.assertEqual(sess["title"], "")
            self.assertEqual(sess["displayName"], sid[:8])
            self.assertFalse(sess["canRenameSession"])

    def test_claude_load_session_includes_title_fields(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            proj = pd / "my-project"
            proj.mkdir()
            sid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            (proj / f"{sid}.jsonl").write_text(
                json.dumps({"type": "user", "content": "hi", "timestamp": "2025-01-01T00:00:00Z"}) + "\n"
            )
            adapter = ClaudeAdapter(pd)
            data = adapter.load_session(sid)
            self.assertIsNotNone(data)
            self.assertEqual(data["title"], "")
            self.assertEqual(data["displayName"], sid[:8])
            self.assertFalse(data["canRenameSession"])


class TestSessionIdRemainsUniqueKey(unittest.TestCase):
    """6.1.1 — session id is always the unique identifier, not title/displayName."""

    def test_codex_load_session_uses_session_id(self):
        """load_session requires session_id, not displayName."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            adapter = CodexAdapter(pd)
            # Should return None for nonexistent session (searched by id, not title)
            result = adapter.load_session("nonexistent-title-not-id")
            self.assertIsNone(result)

    def test_opencode_load_session_uses_session_id(self):
        """load_session requires session_id, not displayName."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT, directory TEXT, "
                "agent TEXT, model TEXT, time_created REAL, time_updated REAL, "
                "tokens_input INT, tokens_output INT, tokens_reasoning INT, "
                "tokens_cache_read INT, tokens_cache_write INT, cost REAL, project_id TEXT)"
            )
            conn.execute(
                "INSERT INTO session (id, title, directory, agent) VALUES (?, ?, ?, ?)",
                ("real-session-id", "My Title", "/tmp/proj", "opencode"),
            )
            conn.commit()
            conn.close()
            adapter = OpenCodeAdapter(pd)
            # Load by id works
            result = adapter.load_session("real-session-id")
            # Title is not a lookup key
            result_by_title = adapter.load_session("My Title")
            self.assertIsNone(result_by_title)


# ---------------------------------------------------------------------------
# 6.2 Codex SQLite rename tests
# ---------------------------------------------------------------------------


class TestCodexRename(unittest.TestCase):
    """Codex SQLite title read/write tests."""

    def _make_codex_env(self, tmp: str, sessions: list[tuple[str, str]] | None = None):
        """Create a minimal Codex environment with rollout + SQLite."""
        pd = Path(tmp) / "sessions"
        session_dir = pd / "2025" / "06" / "03"
        session_dir.mkdir(parents=True)

        sqlite_path = Path(tmp) / "state_5.sqlite"
        conn = sqlite3.connect(str(sqlite_path))
        conn.execute(
            "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
            "model TEXT, model_provider TEXT, updated_at TEXT, tokens_used INT, "
            "created_at TEXT, rollout_path TEXT)"
        )
        sids = []
        for sid, title in (sessions or [("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "Original Title")]):
            fname = f"rollout-2025-06-03T10-00-00-{sid}.jsonl"
            (session_dir / fname).write_text(json.dumps({
                "type": "response_item",
                "timestamp": "2025-06-01T10:00:01Z",
                "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]},
            }) + "\n")
            conn.execute(
                "INSERT INTO threads (id, title, cwd) VALUES (?, ?, ?)",
                (sid, title, "/tmp/project"),
            )
            sids.append(sid)
        conn.commit()
        conn.close()

        adapter = CodexAdapter(pd)
        adapter._sqlite_path = sqlite_path
        return adapter, sids

    def test_codex_list_projects_reads_title(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            projects = adapter.list_projects()
            self.assertTrue(len(projects) > 0)
            sess = projects[0]["sessions"][0]
            self.assertEqual(sess["title"], "Original Title")
            self.assertEqual(sess["displayName"], "Original Title")
            self.assertTrue(sess["canRenameSession"])

    def test_codex_load_session_reads_title(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            data = adapter.load_session(sids[0])
            self.assertIsNotNone(data)
            self.assertEqual(data["title"], "Original Title")
            self.assertEqual(data["displayName"], "Original Title")
            self.assertTrue(data["canRenameSession"])

    def test_codex_rename_success(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            result = adapter.rename_session(sids[0], "New Name")
            self.assertEqual(result["title"], "New Name")
            self.assertEqual(result["displayName"], "New Name")
            self.assertTrue(result["canRenameSession"])
            # Verify DB was updated
            conn = sqlite3.connect(str(adapter._sqlite_path))
            cur = conn.execute("SELECT title FROM threads WHERE id = ?", (sids[0],))
            row = cur.fetchone()
            conn.close()
            self.assertEqual(row[0], "New Name")

    def test_codex_rename_trims_whitespace(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            result = adapter.rename_session(sids[0], "  Trimmed  ")
            self.assertEqual(result["title"], "Trimmed")

    def test_codex_rename_empty_title_raises(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session(sids[0], "   ")
            self.assertEqual(ctx.exception.code, "invalid_title")

    def test_codex_rename_row_missing(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("nonexistent-id-1234-5678-abcdefabcdef", "Name")
            self.assertEqual(ctx.exception.code, "session_not_found")

    def test_codex_rename_schema_missing(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute("CREATE TABLE other_table (id TEXT)")
            conn.commit()
            conn.close()
            adapter = CodexAdapter(pd)
            adapter._sqlite_path = sqlite_path
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("any-id", "Name")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")

    def test_codex_rename_db_not_found(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            adapter = CodexAdapter(pd)
            adapter._sqlite_path = Path(tmp) / "nonexistent.sqlite"
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("any-id", "Name")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")

    def test_codex_rename_readonly_db(self):
        """DB exists but is not writable."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
                "model TEXT, model_provider TEXT, updated_at TEXT, tokens_used INT, "
                "created_at TEXT, rollout_path TEXT)"
            )
            conn.execute("INSERT INTO threads (id, title) VALUES (?, ?)", ("test-id", "Old"))
            conn.commit()
            conn.close()
            sqlite_path.chmod(0o444)
            try:
                adapter = CodexAdapter(pd)
                adapter._sqlite_path = sqlite_path
                with self.assertRaises(SessionRenameError) as ctx:
                    adapter.rename_session("test-id", "New")
                self.assertIn(ctx.exception.code, ("native_title_write_failed",))
            finally:
                sqlite_path.chmod(0o644)

    def test_codex_rename_cache_refresh(self):
        """After rename, list_projects returns new title."""
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_codex_env(tmp)
            # Prime the cache
            adapter.list_projects()
            self.assertIsNotNone(adapter._sqlite_cache)
            # Rename
            adapter.rename_session(sids[0], "Updated Title")
            # Cache should be invalidated
            self.assertIsNone(adapter._sqlite_cache)
            # Subsequent list should show new title
            projects = adapter.list_projects()
            sess = projects[0]["sessions"][0]
            self.assertEqual(sess["title"], "Updated Title")


# ---------------------------------------------------------------------------
# 6.3 OpenCode SQLite rename tests
# ---------------------------------------------------------------------------


class TestOpenCodeRename(unittest.TestCase):
    """OpenCode SQLite title read/write tests."""

    def _make_opencode_env(self, tmp: str, sessions: list[tuple[str, str]] | None = None):
        """Create a minimal OpenCode DB environment."""
        pd = Path(tmp)
        db_path = pd / "opencode.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT, directory TEXT, "
            "agent TEXT, model TEXT, time_created REAL, time_updated REAL, "
            "tokens_input INT, tokens_output INT, tokens_reasoning INT, "
            "tokens_cache_read INT, tokens_cache_write INT, cost REAL, project_id TEXT)"
        )
        conn.execute(
            "CREATE TABLE project (id TEXT PRIMARY KEY, name TEXT, worktree TEXT)"
        )
        conn.execute(
            "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, role TEXT, "
            "time_created REAL)"
        )
        conn.execute(
            "CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, data TEXT, "
            "time_created REAL)"
        )
        conn.execute(
            "CREATE TABLE session_message (session_id TEXT, message_id TEXT)"
        )
        sids = []
        for sid, title in (sessions or [("oc-session-001", "OpenCode Title")]):
            conn.execute(
                "INSERT INTO session (id, title, directory, agent, time_created) VALUES (?, ?, ?, ?, ?)",
                (sid, title, "/tmp/project", "opencode", 1700000000),
            )
            sids.append(sid)
        conn.commit()
        conn.close()

        adapter = OpenCodeAdapter(pd)
        return adapter, sids

    def test_opencode_list_projects_reads_title(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_opencode_env(tmp)
            projects = adapter.list_projects()
            self.assertTrue(len(projects) > 0)
            sess = projects[0]["sessions"][0]
            self.assertEqual(sess["title"], "OpenCode Title")
            self.assertEqual(sess["displayName"], "OpenCode Title")
            self.assertTrue(sess["canRenameSession"])

    def test_opencode_rename_success(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_opencode_env(tmp)
            result = adapter.rename_session(sids[0], "New OC Name")
            self.assertEqual(result["title"], "New OC Name")
            self.assertEqual(result["displayName"], "New OC Name")
            self.assertTrue(result["canRenameSession"])
            # Verify DB updated
            db_path = Path(tmp) / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            cur = conn.execute("SELECT title FROM session WHERE id = ?", (sids[0],))
            row = cur.fetchone()
            conn.close()
            self.assertEqual(row[0], "New OC Name")

    def test_opencode_rename_trims_whitespace(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_opencode_env(tmp)
            result = adapter.rename_session(sids[0], "  Spaced  ")
            self.assertEqual(result["title"], "Spaced")

    def test_opencode_rename_empty_title_raises(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_opencode_env(tmp)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session(sids[0], "")
            self.assertEqual(ctx.exception.code, "invalid_title")

    def test_opencode_rename_row_missing(self):
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_opencode_env(tmp)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("nonexistent-session-id", "Name")
            self.assertEqual(ctx.exception.code, "session_not_found")

    def test_opencode_rename_schema_missing(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE other (id TEXT)")
            conn.commit()
            conn.close()
            adapter = OpenCodeAdapter(pd)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("any-id", "Name")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")

    def test_opencode_rename_db_not_found(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "subdir"
            pd.mkdir()
            adapter = OpenCodeAdapter(pd)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("any-id", "Name")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")

    def test_opencode_rename_does_not_modify_messages(self):
        """Rename must not touch message/part tables."""
        with TemporaryDirectory() as tmp:
            adapter, sids = self._make_opencode_env(tmp)
            db_path = Path(tmp) / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute("INSERT INTO message (id, session_id, role) VALUES (?, ?, ?)",
                         ("msg1", sids[0], "user"))
            conn.execute("INSERT INTO part (id, message_id, data) VALUES (?, ?, ?)",
                         ("part1", "msg1", '{"text": "hello"}'))
            conn.commit()
            conn.close()
            adapter.rename_session(sids[0], "Renamed")
            # Verify messages unchanged
            conn = sqlite3.connect(str(db_path))
            cur = conn.execute("SELECT data FROM part WHERE id = 'part1'")
            row = cur.fetchone()
            conn.close()
            self.assertEqual(row[0], '{"text": "hello"}')


# ---------------------------------------------------------------------------
# 6.4 Viewer server API tests
# ---------------------------------------------------------------------------


class TestViewerRenameAPI(unittest.TestCase):
    """Test POST /api/session/<sessionId>/rename endpoint."""

    def _make_server(self, adapter):
        """Create a test server with the given adapter."""
        from http.server import HTTPServer
        from viewer.server import create_server
        server = create_server(
            port=0,  # auto-assign
            projects_dir=Path("/tmp"),
            logs_dir=Path("/tmp"),
            adapter=adapter,
        )
        return server

    def _request(self, server, method, path, body=None):
        """Send a request to the server handler directly."""
        import io
        from http.server import BaseHTTPRequestHandler
        from unittest.mock import MagicMock

        handler_class = server.RequestHandlerClass

        # Build the raw HTTP request
        body_bytes = json.dumps(body).encode() if body else b""

        # rfile should contain only the body (headers are parsed separately)
        rfile = io.BytesIO(body_bytes)
        wfile = io.BytesIO()

        # Mock the connection
        handler = handler_class.__new__(handler_class)
        handler.rfile = rfile
        handler.wfile = wfile
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.command = method
        handler.path = path
        handler.request_version = "HTTP/1.1"
        handler.close_connection = True
        handler.client_address = ("127.0.0.1", 0)
        handler.server = server
        handler.log_request = lambda *a, **kw: None
        handler.log_error = lambda *a, **kw: None

        # Parse headers properly
        import email.parser
        header_text = f"Content-Type: application/json\r\nContent-Length: {len(body_bytes)}\r\n"
        handler.headers = email.parser.Parser().parsestr(header_text)

        # Call the handler
        if method == "POST":
            handler.do_POST()
        elif method == "GET":
            handler.do_GET()

        # Parse response
        wfile.seek(0)
        response_data = wfile.read().decode("utf-8", errors="replace")
        # Find JSON body
        parts = response_data.split("\r\n\r\n", 1)
        status_line = parts[0].split("\r\n")[0] if parts else ""
        status_code = int(status_line.split(" ")[1]) if " " in status_line else 500
        body_text = parts[1] if len(parts) > 1 else ""
        try:
            result = json.loads(body_text)
        except json.JSONDecodeError:
            result = {"raw": body_text}
        return status_code, result

    def test_rename_codex_success(self):
        with TemporaryDirectory() as tmp:
            # Setup codex adapter with DB
            pd = Path(tmp) / "sessions"
            session_dir = pd / "2025" / "06" / "03"
            session_dir.mkdir(parents=True)
            sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            fname = f"rollout-2025-06-03T10-00-00-{sid}.jsonl"
            (session_dir / fname).write_text(json.dumps({
                "type": "response_item",
                "timestamp": "2025-06-01T10:00:01Z",
                "payload": {"type": "message", "role": "user",
                            "content": [{"type": "input_text", "text": "hi"}]},
            }) + "\n")
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
                "model TEXT, model_provider TEXT, updated_at TEXT, tokens_used INT, "
                "created_at TEXT, rollout_path TEXT)"
            )
            conn.execute("INSERT INTO threads (id, title, cwd) VALUES (?, ?, ?)",
                         (sid, "Old", "/tmp"))
            conn.commit()
            conn.close()

            adapter = CodexAdapter(pd)
            adapter._sqlite_path = sqlite_path
            server = self._make_server(adapter)
            status, result = self._request(server, "POST",
                                           f"/api/session/{sid}/rename",
                                           {"title": "New Name"})
            self.assertEqual(status, 200)
            self.assertTrue(result["ok"])
            self.assertEqual(result["agent"], "codex")
            self.assertEqual(result["sessionId"], sid)
            self.assertEqual(result["title"], "New Name")
            self.assertEqual(result["displayName"], "New Name")
            self.assertTrue(result["canRenameSession"])

    def test_rename_invalid_title_empty(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            adapter = CodexAdapter(pd)
            server = self._make_server(adapter)
            status, result = self._request(server, "POST",
                                           "/api/session/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/rename",
                                           {"title": "   "})
            self.assertEqual(status, 400)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "invalid_title")

    def test_rename_session_not_found(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            session_dir = pd / "2025" / "06" / "03"
            session_dir.mkdir(parents=True)
            sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            fname = f"rollout-2025-06-03T10-00-00-{sid}.jsonl"
            (session_dir / fname).write_text(json.dumps({
                "type": "response_item", "timestamp": "2025-06-01T10:00:01Z",
                "payload": {"type": "message", "role": "user",
                            "content": [{"type": "input_text", "text": "hi"}]},
            }) + "\n")
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
                "model TEXT, model_provider TEXT, updated_at TEXT, tokens_used INT, "
                "created_at TEXT, rollout_path TEXT)"
            )
            # Note: no row inserted for the session
            conn.commit()
            conn.close()
            adapter = CodexAdapter(pd)
            adapter._sqlite_path = sqlite_path
            server = self._make_server(adapter)
            status, result = self._request(server, "POST",
                                           f"/api/session/{sid}/rename",
                                           {"title": "Name"})
            self.assertEqual(status, 404)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "session_not_found")

    def test_rename_claude_unsupported(self):
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            proj = pd / "my-project"
            proj.mkdir()
            sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            (proj / f"{sid}.jsonl").write_text(
                json.dumps({"type": "user", "content": "hi", "timestamp": "2025-01-01T00:00:00Z"}) + "\n"
            )
            adapter = ClaudeAdapter(pd)
            server = self._make_server(adapter)
            status, result = self._request(server, "POST",
                                           f"/api/session/{sid}/rename",
                                           {"title": "Name"})
            self.assertEqual(status, 501)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "rename_not_supported")

    def test_rename_opencode_schema_missing_returns_500(self):
        """API returns 500 native_title_unavailable when session table lacks title column."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            # Session table WITHOUT title column
            conn.execute(
                "CREATE TABLE session (id TEXT PRIMARY KEY, directory TEXT, "
                "agent TEXT, model TEXT, time_created REAL)"
            )
            conn.execute(
                "CREATE TABLE project (id TEXT PRIMARY KEY, name TEXT, worktree TEXT)"
            )
            sid = "oc-schema-miss-0001-0000-000000000001"
            conn.execute(
                "INSERT INTO session (id, directory, agent, time_created) VALUES (?, ?, ?, ?)",
                (sid, "/tmp/proj", "opencode", 1700000000),
            )
            conn.commit()
            conn.close()
            adapter = OpenCodeAdapter(pd)
            server = self._make_server(adapter)
            status, result = self._request(server, "POST",
                                           f"/api/session/{sid}/rename",
                                           {"title": "New Name"})
            self.assertEqual(status, 500)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "native_title_unavailable")

    def test_rename_codex_schema_missing_returns_500(self):
        """API returns 500 native_title_unavailable when threads table lacks title column."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            # threads table WITHOUT title column
            conn.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, cwd TEXT)"
            )
            sid = "cx-schema-miss-0001-0000-000000000001"
            conn.execute("INSERT INTO threads (id, cwd) VALUES (?, ?)", (sid, "/tmp"))
            conn.commit()
            conn.close()
            adapter = CodexAdapter(pd)
            adapter._sqlite_path = sqlite_path
            server = self._make_server(adapter)
            status, result = self._request(server, "POST",
                                           f"/api/session/{sid}/rename",
                                           {"title": "New Name"})
            self.assertEqual(status, 500)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "native_title_unavailable")

    def test_rename_opencode_write_failed_returns_500(self):
        """API returns 500 native_title_write_failed on SQLite write failure."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT, directory TEXT, "
                "agent TEXT, model TEXT, time_created REAL, time_updated REAL, "
                "tokens_input INT, tokens_output INT, tokens_reasoning INT, "
                "tokens_cache_read INT, tokens_cache_write INT, cost REAL, project_id TEXT)"
            )
            sid = "oc-write-fail-0001-0000-000000000001"
            conn.execute(
                "INSERT INTO session (id, title, directory, agent, time_created) VALUES (?, ?, ?, ?, ?)",
                (sid, "Old", "/tmp/proj", "opencode", 1700000000),
            )
            conn.commit()
            conn.close()
            adapter = OpenCodeAdapter(pd)
            server = self._make_server(adapter)
            # Patch rename_session to raise native_title_write_failed
            def _raise_write_failed(session_id, title):
                raise SessionRenameError("native_title_write_failed", "disk full")
            adapter.rename_session = _raise_write_failed
            status, result = self._request(server, "POST",
                                           f"/api/session/{sid}/rename",
                                           {"title": "New Name"})
            self.assertEqual(status, 500)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "native_title_write_failed")

    def test_rename_codex_readonly_returns_500_via_api(self):
        """API returns 500 when Codex DB is read-only."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT)"
            )
            sid = "cx-readonly-db-0001-0000-000000000001"
            conn.execute("INSERT INTO threads (id, title, cwd) VALUES (?, ?, ?)",
                         (sid, "Old", "/tmp"))
            conn.commit()
            conn.close()
            sqlite_path.chmod(0o444)
            try:
                adapter = CodexAdapter(pd)
                adapter._sqlite_path = sqlite_path
                server = self._make_server(adapter)
                status, result = self._request(server, "POST",
                                               f"/api/session/{sid}/rename",
                                               {"title": "New Name"})
                self.assertEqual(status, 500)
                self.assertFalse(result["ok"])
                self.assertEqual(result["code"], "native_title_write_failed")
            finally:
                sqlite_path.chmod(0o644)


# ---------------------------------------------------------------------------
# 6.4b Adapter 500-class error tests (schema missing, write failures)
# ---------------------------------------------------------------------------


class TestAdapterErrorCodes(unittest.TestCase):
    """Adapter-level tests for native_title_unavailable and write_failed codes."""

    def test_opencode_title_column_missing_raises_unavailable(self):
        """Session exists but title column missing → native_title_unavailable, not session_not_found."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE session (id TEXT PRIMARY KEY, directory TEXT, agent TEXT)"
            )
            conn.execute(
                "INSERT INTO session (id, directory, agent) VALUES (?, ?, ?)",
                ("existing-session-id-123456789012", "/tmp/proj", "opencode"),
            )
            conn.commit()
            conn.close()
            adapter = OpenCodeAdapter(pd)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("existing-session-id-123456789012", "New Title")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")
            self.assertIn("title", ctx.exception.message.lower())

    def test_codex_title_column_missing_raises_unavailable(self):
        """Thread exists but title column missing → native_title_unavailable."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, cwd TEXT)")
            conn.execute("INSERT INTO threads (id, cwd) VALUES (?, ?)",
                         ("existing-thread-id-123456789012", "/tmp"))
            conn.commit()
            conn.close()
            adapter = CodexAdapter(pd)
            adapter._sqlite_path = sqlite_path
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("existing-thread-id-123456789012", "New Title")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")

    def test_opencode_readonly_db_raises_write_failed(self):
        """OpenCode DB is read-only → native_title_write_failed."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT, directory TEXT, "
                "agent TEXT, time_created REAL)"
            )
            conn.execute(
                "INSERT INTO session (id, title, directory, agent, time_created) VALUES (?, ?, ?, ?, ?)",
                ("oc-ro-sess-000000000000000000001", "Old", "/tmp", "opencode", 1700000000),
            )
            conn.commit()
            conn.close()
            db_path.chmod(0o444)
            try:
                adapter = OpenCodeAdapter(pd)
                with self.assertRaises(SessionRenameError) as ctx:
                    adapter.rename_session("oc-ro-sess-000000000000000000001", "New")
                self.assertEqual(ctx.exception.code, "native_title_write_failed")
            finally:
                db_path.chmod(0o644)

    def test_opencode_session_table_missing_raises_unavailable(self):
        """DB exists but session table doesn't → native_title_unavailable."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp)
            db_path = pd / "opencode.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE something_else (id TEXT)")
            conn.commit()
            conn.close()
            adapter = OpenCodeAdapter(pd)
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("any-session-id-0000000000001", "Title")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")
            self.assertIn("session", ctx.exception.message.lower())

    def test_codex_threads_table_missing_raises_unavailable(self):
        """DB exists but threads table doesn't → native_title_unavailable."""
        with TemporaryDirectory() as tmp:
            pd = Path(tmp) / "sessions"
            pd.mkdir(parents=True)
            sqlite_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute("CREATE TABLE something_else (id TEXT)")
            conn.commit()
            conn.close()
            adapter = CodexAdapter(pd)
            adapter._sqlite_path = sqlite_path
            with self.assertRaises(SessionRenameError) as ctx:
                adapter.rename_session("any-id-000000000000000000001", "Title")
            self.assertEqual(ctx.exception.code, "native_title_unavailable")
            self.assertIn("threads", ctx.exception.message.lower())


# ---------------------------------------------------------------------------
# 6.5 Frontend static / DOM smoke tests
# ---------------------------------------------------------------------------


_HTML = (Path(__file__).resolve().parents[1] / "viewer" / "claude-log.html").read_text(encoding="utf-8")


class TestRenameFrontendElements(unittest.TestCase):
    """Frontend smoke tests for rename UI elements."""

    def test_session_title_bar_exists(self):
        self.assertIn('id="sessionTitleBar"', _HTML)

    def test_session_display_name_element(self):
        self.assertIn('id="sessionDisplayName"', _HTML)

    def test_session_id_label_element(self):
        self.assertIn('id="sessionIdLabel"', _HTML)

    def test_rename_button_exists(self):
        self.assertIn('id="sessionRenameBtn"', _HTML)
        self.assertIn('onclick="startSessionRename()"', _HTML)

    def test_rename_unsupported_label(self):
        self.assertIn('id="sessionRenameUnsupported"', _HTML)
        self.assertIn('不支持重命名', _HTML)

    def test_rename_form_elements(self):
        self.assertIn('id="sessionRenameForm"', _HTML)
        self.assertIn('id="sessionRenameInput"', _HTML)
        self.assertIn('id="sessionRenameSaveBtn"', _HTML)
        self.assertIn('id="sessionRenameCancelBtn"', _HTML)

    def test_rename_endpoint_called(self):
        self.assertIn('/api/session/', _HTML)
        self.assertIn('/rename', _HTML)

    def test_can_rename_session_controls_edit(self):
        """canRenameSession check in updateSessionTitleBar."""
        self.assertIn('canRenameSession', _HTML)
        self.assertIn("canRename", _HTML)

    def test_display_name_in_selector(self):
        """fmtSessionLabel uses displayName."""
        self.assertIn('s.displayName', _HTML)

    def test_save_success_updates_state(self):
        """After rename success, allProjects and selector are updated."""
        self.assertIn('sess.title = result.title', _HTML)
        self.assertIn('sess.displayName = result.displayName', _HTML)

    def test_save_failure_shows_error(self):
        """On failure, error is displayed."""
        self.assertIn('保存失败', _HTML)

    def test_session_id_visible_in_title_bar(self):
        """session id is shown alongside displayName."""
        self.assertIn('sessionIdLabel', _HTML)

    def test_cancel_does_not_call_api(self):
        """cancelSessionRename hides form without fetch."""
        # The cancel function only changes display, no fetch call
        fn_start = _HTML.index("function cancelSessionRename()")
        fn_end = _HTML.index("async function saveSessionRename()", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertNotIn("fetch(", snippet)

    def test_stale_session_guard_in_success_path(self):
        """saveSessionRename checks current session before updating UI on success."""
        fn_start = _HTML.index("async function saveSessionRename()")
        fn_end = _HTML.index("}", _HTML.index("} finally {", fn_start)) + 2
        snippet = _HTML[fn_start:fn_end]
        # Must have stale check after fetch (currentSession !== sessionId)
        self.assertIn("currentSession !== sessionId", snippet)

    def test_stale_session_guard_in_error_path(self):
        """saveSessionRename checks current session before updating UI on error."""
        fn_start = _HTML.index("async function saveSessionRename()")
        fn_end = _HTML.index("}", _HTML.index("} finally {", fn_start)) + 2
        snippet = _HTML[fn_start:fn_end]
        # Must appear multiple times: success path, error resp path, catch path
        first = snippet.index("currentSession !== sessionId")
        second = snippet.index("currentSession !== sessionId", first + 1)
        third = snippet.index("currentSession !== sessionId", second + 1)
        self.assertIsNotNone(third)

    def test_stale_guard_still_updates_allprojects_cache(self):
        """Even on stale session, allProjects cache is updated before guard check."""
        fn_start = _HTML.index("async function saveSessionRename()")
        fn_end = _HTML.index("}", _HTML.index("} finally {", fn_start)) + 2
        snippet = _HTML[fn_start:fn_end]
        # allProjects update must come before the stale guard
        cache_pos = snippet.index("sess.title = result.title")
        stale_pos = snippet.index("currentSession !== sessionId", snippet.index("sess.title"))
        self.assertLess(cache_pos, stale_pos)


# ---------------------------------------------------------------------------
# 6.6 Non-regression: existing adapter tests still pass (run separately)
# ---------------------------------------------------------------------------

class TestNonRegressionImports(unittest.TestCase):
    """Verify key modules still import cleanly."""

    def test_import_adapters(self):
        from ccwhat.adapters.base import AgentAdapter, SessionRenameError
        from ccwhat.adapters.claude import ClaudeAdapter
        from ccwhat.adapters.codex import CodexAdapter
        from ccwhat.adapters.opencode import OpenCodeAdapter
        from ccwhat.adapters.registry import create_adapter

    def test_import_viewer_server(self):
        from viewer.server import create_server


if __name__ == "__main__":
    unittest.main()
