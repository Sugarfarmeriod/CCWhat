from __future__ import annotations

import importlib.util
import builtins
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from ccwhat.commands.proxy import proxy


REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDER_PATH = REPO_ROOT / "ccwhat" / "addons" / "recorder.py"


class RecorderIsolationTests(unittest.TestCase):
    def test_recorder_imports_without_ccwhat_package(self) -> None:
        old_modules = dict(sys.modules)
        old_domains = os.environ.get("CCWHAT_RECORD_DOMAINS")
        real_import = builtins.__import__

        mitmproxy = types.ModuleType("mitmproxy")
        mitmproxy.http = types.SimpleNamespace(HTTPFlow=object)

        def isolated_import(name, *args, **kwargs):
            if name == "ccwhat" or name.startswith("ccwhat."):
                raise ModuleNotFoundError("No module named 'ccwhat'")
            return real_import(name, *args, **kwargs)

        try:
            sys.modules["mitmproxy"] = mitmproxy
            sys.modules["mitmproxy.http"] = mitmproxy.http
            sys.modules.pop("ccwhat", None)
            sys.modules.pop("ccwhat.config", None)
            os.environ["CCWHAT_RECORD_DOMAINS"] = "api.anthropic.com, other.example.com"

            with mock.patch("builtins.__import__", side_effect=isolated_import):
                spec = importlib.util.spec_from_file_location("isolated_recorder", RECORDER_PATH)
                self.assertIsNotNone(spec)
                assert spec is not None
                self.assertIsNotNone(spec.loader)
                assert spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            addon = module.RecorderAddon()

            self.assertEqual(addon._domains, ["api.anthropic.com", "other.example.com"])
        finally:
            sys.modules.clear()
            sys.modules.update(old_modules)
            if old_domains is None:
                os.environ.pop("CCWHAT_RECORD_DOMAINS", None)
            else:
                os.environ["CCWHAT_RECORD_DOMAINS"] = old_domains

    def test_proxy_passes_record_domains_to_mitmdump_addon(self) -> None:
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("ccwhat.commands.proxy.subprocess.run") as run:
                run.return_value.returncode = 0

                # Proxy needs a valid config or --domain; use --domain for this test
                result = runner.invoke(proxy, ["--port", "7799", "--output", tmp, "--domain", "api.anthropic.com"])

        self.assertEqual(result.exit_code, 0, result.output)
        env = run.call_args.kwargs["env"]
        self.assertIn("api.anthropic.com", env["CCWHAT_RECORD_DOMAINS"])

    def test_proxy_requires_domains_in_non_interactive_mode(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            # Non-interactive (no tty), no domains, no config
            import io as _io
            with mock.patch("ccwhat.commands.proxy.load_config", return_value=None):
                result = runner.invoke(proxy, ["--port", "7799", "--output", tmp], input=None)
        # Should fail with actionable error
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("ccwhat setup", result.output)

    def test_recorder_redacts_sensitive_headers(self) -> None:
        """Recorder should redact authorization, cookie, and pattern-matched headers."""
        old_modules = dict(sys.modules)
        mitmproxy = types.ModuleType("mitmproxy")
        mitmproxy.http = types.SimpleNamespace(HTTPFlow=object)
        try:
            sys.modules["mitmproxy"] = mitmproxy
            sys.modules["mitmproxy.http"] = mitmproxy.http
            sys.modules.pop("ccwhat", None)
            spec = importlib.util.spec_from_file_location("isolated_recorder", RECORDER_PATH)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            addon = module.RecorderAddon()
            # Sensitive header should be redacted
            headers = {
                "authorization": "Bearer secret-token",
                "x-api-key": "sk-xxx",
                "content-type": "application/json",
                "x-my-token": "value",
            }
            result = addon._redact_headers_dict(headers)
            self.assertEqual(result["authorization"], "[REDACTED]")
            self.assertEqual(result["x-api-key"], "[REDACTED]")
            self.assertEqual(result["x-my-token"], "[REDACTED]")
            self.assertEqual(result["content-type"], "application/json")
        finally:
            sys.modules.clear()
            sys.modules.update(old_modules)

    def test_recorder_truncates_large_body(self) -> None:
        """Recorder should truncate bodies exceeding max_body_bytes."""
        old_modules = dict(sys.modules)
        mitmproxy = types.ModuleType("mitmproxy")
        mitmproxy.http = types.SimpleNamespace(HTTPFlow=object)
        try:
            sys.modules["mitmproxy"] = mitmproxy
            sys.modules["mitmproxy.http"] = mitmproxy.http
            sys.modules.pop("ccwhat", None)
            spec = importlib.util.spec_from_file_location("isolated_recorder", RECORDER_PATH)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            addon = module.RecorderAddon()
            addon._max_body_bytes = 10
            body, truncated, original_len = addon._limit_body("hello world this is too long")
            self.assertTrue(truncated)
            self.assertLessEqual(len(body.encode("utf-8")), 10)
            self.assertGreater(original_len, 10)
        finally:
            sys.modules.clear()
            sys.modules.update(old_modules)

    def test_recorder_uses_local_session_id_when_header_missing(self) -> None:
        """Recorder should use local session ID when no X-Claude-Code-Session-Id header."""
        old_modules = dict(sys.modules)
        mitmproxy = types.ModuleType("mitmproxy")
        mitmproxy.http = types.SimpleNamespace(HTTPFlow=object)
        try:
            sys.modules["mitmproxy"] = mitmproxy
            sys.modules["mitmproxy.http"] = mitmproxy.http
            sys.modules.pop("ccwhat", None)
            os.environ["CCWHAT_LOCAL_SESSION_ID"] = "local-test-session-id"
            spec = importlib.util.spec_from_file_location("isolated_recorder", RECORDER_PATH)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            addon = module.RecorderAddon()
            flow = types.SimpleNamespace(request=types.SimpleNamespace(headers={}))
            session_id = addon._get_session_id(flow)
            self.assertEqual(session_id, "local-test-session-id")
        finally:
            sys.modules.clear()
            sys.modules.update(old_modules)
            os.environ.pop("CCWHAT_LOCAL_SESSION_ID", None)


if __name__ == "__main__":
    unittest.main()
