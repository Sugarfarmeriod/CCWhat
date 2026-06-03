from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
from unittest import mock

from ccwhat.analyzer import (
    AnalysisError,
    build_analysis_prompt,
    run_mc_analysis,
    serialize_session_for_analysis,
)
from viewer.server import _make_handler


SID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


def _write_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _make_projects(base: Path) -> Path:
    projects_dir = base / "projects"
    _write_jsonl(
        projects_dir / "project-c" / f"{SID}.jsonl",
        {"type": "user", "timestamp": "2026-05-29T03:00:00Z", "message": {"content": "hello"}},
    )
    _write_jsonl(
        projects_dir / "project-c" / SID / "subagents" / "agent-one.jsonl",
        {"type": "assistant", "timestamp": "2026-05-29T03:01:00Z", "message": {"content": []}},
    )
    (projects_dir / "project-c" / SID / "subagents" / "agent-one.meta.json").write_text(
        json.dumps({"description": "helper"}),
        encoding="utf-8",
    )
    return projects_dir


class AnalysisCoreTests(unittest.TestCase):
    def test_build_prompt_replaces_placeholder_and_marks_truncation(self) -> None:
        session = {
            "sessionId": SID,
            "projectDir": "project-c",
            "main": [{"type": "user", "message": {"content": "x" * 50}}],
            "subagents": [],
        }

        prompt, truncated = build_analysis_prompt(session, template="before {{content}} after", max_chars=180)

        self.assertTrue(truncated)
        self.assertIn("before", prompt)
        self.assertIn("project-c", prompt)
        self.assertIn("[TRUNCATED]", prompt)
        self.assertNotIn("{{content}}", prompt)

    def test_serialize_session_includes_subagents(self) -> None:
        content, truncated = serialize_session_for_analysis({
            "sessionId": SID,
            "projectDir": "project-c",
            "main": [{"type": "user"}],
            "subagents": [{"agentId": "one", "entries": [{"type": "assistant"}]}],
        })

        self.assertFalse(truncated)
        self.assertIn('"sessionId": "cccccccc-cccc-cccc-cccc-cccccccccccc"', content)
        self.assertIn('"agentId": "one"', content)

    def test_run_mc_analysis_maps_failures(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "not found"):
            run_mc_analysis("prompt", runner=mock.Mock(side_effect=FileNotFoundError()))

        with self.assertRaisesRegex(AnalysisError, "timed out"):
            run_mc_analysis("prompt", runner=mock.Mock(side_effect=subprocess.TimeoutExpired("mc", 1)))

        failed = subprocess.CompletedProcess(["mc"], 2, stdout="", stderr="bad")
        with self.assertRaisesRegex(AnalysisError, "bad"):
            run_mc_analysis("prompt", runner=mock.Mock(return_value=failed))

        empty = subprocess.CompletedProcess(["mc"], 0, stdout="", stderr="")
        with self.assertRaisesRegex(AnalysisError, "empty"):
            run_mc_analysis("prompt", runner=mock.Mock(return_value=empty))

    def test_run_mc_analysis_uses_explicit_command(self) -> None:
        completed = subprocess.CompletedProcess(["mc", "--code"], 0, stdout="report", stderr="")
        runner = mock.Mock(return_value=completed)

        report, _ = run_mc_analysis("prompt", runner=runner, cmd=("mc", "--code"))

        self.assertEqual(report, "report")
        call = runner.call_args
        self.assertEqual(call.args[0], ["mc", "--code"])
        self.assertEqual(call.kwargs["input"], "prompt")


class AnalyzeApiTests(unittest.TestCase):
    def _post_analyze(self, server: HTTPServer, payload: dict) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", server.server_port)
        conn.request(
            "POST",
            "/api/analyze",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        body = response.read()
        conn.close()
        return response.status, json.loads(body.decode("utf-8"))

    def test_analyze_api_posts_current_session_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            projects_dir = _make_projects(tmp)
            server = HTTPServer(("127.0.0.1", 0), _make_handler(projects_dir, tmp / "raw"))
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                completed = subprocess.CompletedProcess(["mc"], 0, stdout="Agent 交互分析报告", stderr="")
                with mock.patch("ccwhat.analyzer.subprocess.run", return_value=completed) as run:
                    status, payload = self._post_analyze(server, {"sessionId": SID, "turnKeys": ["main:0"]})
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["report"], "Agent 交互分析报告")
        call = run.call_args
        self.assertEqual(call.args[0][:2], ["claude", "-p"])  # default analyzer cmd
        self.assertIn("hello", call.kwargs["input"])
        self.assertIn("helper", call.kwargs["input"])

    def test_analyze_api_uses_managed_viewer_analyzer_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            projects_dir = _make_projects(tmp)
            server = HTTPServer(
                ("127.0.0.1", 0),
                _make_handler(projects_dir, tmp / "raw", analyzer_cmd=("mc", "--code")),
            )
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                completed = subprocess.CompletedProcess(["mc", "--code"], 0, stdout="report", stderr="")
                with mock.patch("ccwhat.analyzer.subprocess.run", return_value=completed) as run:
                    status, payload = self._post_analyze(server, {"sessionId": SID})
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["report"], "report")
        call = run.call_args
        self.assertEqual(call.args[0], ["mc", "--code"])
        self.assertIn("hello", call.kwargs["input"])

    def test_analyze_api_handles_missing_session_and_mc_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            projects_dir = _make_projects(tmp)
            server = HTTPServer(("127.0.0.1", 0), _make_handler(projects_dir, tmp / "raw"))
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                missing_status, missing_payload = self._post_analyze(
                    server,
                    {"sessionId": "dddddddd-dddd-dddd-dddd-dddddddddddd"},
                )
                with mock.patch("ccwhat.analyzer.subprocess.run", side_effect=FileNotFoundError()):
                    error_status, error_payload = self._post_analyze(server, {"sessionId": SID})
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

        self.assertEqual(missing_status, 404, missing_payload)
        self.assertFalse(missing_payload["ok"])
        self.assertEqual(error_status, 500, error_payload)
        self.assertEqual(error_payload["code"], "analyzer_not_found")


class AnalyzeFrontendTests(unittest.TestCase):
    def test_frontend_uses_current_session_only(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "viewer" / "claude-log.html").read_text(encoding="utf-8")

        self.assertIn('id="analyzeBtn"', html)
        self.assertIn("分析当前 Session", html)
        self.assertIn("analyzeCurrentSession()", html)
        self.assertIn("fetch(`${apiBase()}/api/analyze`", html)
        self.assertIn("body: JSON.stringify({sessionId})", html)
        self.assertNotIn("turnKeys", html)

    def test_frontend_caches_reports_and_supports_reanalysis(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "viewer" / "claude-log.html").read_text(encoding="utf-8")

        self.assertIn("const analysisReports = {}", html)
        self.assertIn("analysisReports[sessionId] = cached", html)
        self.assertIn("analysisReports[sessionId] ? '查看分析报告' : '分析当前 Session'", html)
        self.assertIn("function showCachedAnalysisReport()", html)
        self.assertIn("function reanalyzeCurrentSession()", html)
        self.assertIn("preserveCached && previous", html)
        self.assertIn("analysisReports[sessionId] = previous", html)
        self.assertIn("重新分析失败", html)

    def test_frontend_renders_analysis_markdown_richly(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "viewer" / "claude-log.html").read_text(encoding="utf-8")

        self.assertIn("function renderMarkdownInline", html)
        self.assertIn("function splitMarkdownTableRow", html)
        self.assertIn("function isMarkdownTableSeparator", html)
        self.assertIn('class="md-table-wrap"', html)
        self.assertIn('data-lang="${escRaw(lang)}"', html)
        self.assertIn('class="md-code-block"', html)
        self.assertIn(".md-view table", html)
        self.assertIn(".md-view th", html)
        self.assertIn(".md-view blockquote", html)
        self.assertIn("cdn.jsdelivr.net/npm/mermaid@10", html)
        self.assertIn('class="md-mermaid-wrap"', html)
        self.assertIn('class="md-mermaid"', html)
        self.assertIn("function renderMermaidBlocks", html)
        self.assertIn("function fallbackMermaidBlock", html)
        self.assertIn("window.mermaid.run", html)
        self.assertIn("renderMermaidBlocks(body)", html)
        self.assertIn("library unavailable", html)
        self.assertIn("render failed", html)
        self.assertIn(".replace(/</g,'&lt;')", html)
        self.assertIn(".replace(/>/g,'&gt;')", html)


if __name__ == "__main__":
    unittest.main()
