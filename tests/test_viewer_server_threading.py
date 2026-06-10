"""Viewer server construction tests."""

from __future__ import annotations

import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from viewer.server import create_server


class TestViewerServerThreading(unittest.TestCase):
    def test_create_server_uses_threading_http_server(self) -> None:
        server = create_server(0, Path("."), Path("."))
        try:
            self.assertIsInstance(server, ThreadingHTTPServer)
            self.assertTrue(server.daemon_threads)
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
