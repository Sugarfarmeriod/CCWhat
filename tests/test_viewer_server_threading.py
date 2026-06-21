"""Viewer server construction tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from viewer.server import ViewerServer, create_server


class TestViewerServerThreading(unittest.TestCase):
    def test_create_server_returns_viewer_server(self) -> None:
        server = create_server(0, Path("."), Path("."))
        try:
            self.assertIsInstance(server, ViewerServer)
            self.assertTrue(server.daemon_threads)
            self.assertTrue(callable(server.serve_forever))
            self.assertTrue(callable(server.shutdown))
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
