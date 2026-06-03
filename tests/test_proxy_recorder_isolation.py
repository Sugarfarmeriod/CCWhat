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

from deep_ai_analysis.commands.proxy import proxy


REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDER_PATH = REPO_ROOT / "deep_ai_analysis" / "addons" / "recorder.py"


class RecorderIsolationTests(unittest.TestCase):
    def test_recorder_imports_without_deep_ai_analysis_package(self) -> None:
        old_modules = dict(sys.modules)
        old_domains = os.environ.get("DAA_RECORD_DOMAINS")
        real_import = builtins.__import__

        mitmproxy = types.ModuleType("mitmproxy")
        mitmproxy.http = types.SimpleNamespace(HTTPFlow=object)

        def isolated_import(name, *args, **kwargs):
            if name == "deep_ai_analysis" or name.startswith("deep_ai_analysis."):
                raise ModuleNotFoundError("No module named 'deep_ai_analysis'")
            return real_import(name, *args, **kwargs)

        try:
            sys.modules["mitmproxy"] = mitmproxy
            sys.modules["mitmproxy.http"] = mitmproxy.http
            sys.modules.pop("deep_ai_analysis", None)
            sys.modules.pop("deep_ai_analysis.config", None)
            os.environ["DAA_RECORD_DOMAINS"] = "mcli.sankuai.com, other.example.com"

            with mock.patch("builtins.__import__", side_effect=isolated_import):
                spec = importlib.util.spec_from_file_location("isolated_recorder", RECORDER_PATH)
                self.assertIsNotNone(spec)
                assert spec is not None
                self.assertIsNotNone(spec.loader)
                assert spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            addon = module.RecorderAddon()

            self.assertEqual(addon._domains, ["mcli.sankuai.com", "other.example.com"])
        finally:
            sys.modules.clear()
            sys.modules.update(old_modules)
            if old_domains is None:
                os.environ.pop("DAA_RECORD_DOMAINS", None)
            else:
                os.environ["DAA_RECORD_DOMAINS"] = old_domains

    def test_proxy_passes_record_domains_to_mitmdump_addon(self) -> None:
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("deep_ai_analysis.commands.proxy.subprocess.run") as run:
                run.return_value.returncode = 0

                result = runner.invoke(proxy, ["--port", "7799", "--output", tmp])

        self.assertEqual(result.exit_code, 0, result.output)
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["DAA_RECORD_DOMAINS"], "mcli.sankuai.com")


if __name__ == "__main__":
    unittest.main()
