"""Port allocation helpers for runtime runs."""

from __future__ import annotations

import socket


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def allocate_port(exclude: set[int] | None = None) -> int:
    exclude = exclude or set()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = int(sock.getsockname()[1])
        if port not in exclude:
            return port


def resolve_runtime_ports(
    *,
    proxy_port: int | None,
    viewer_port: int | None,
    need_viewer: bool,
) -> tuple[int, int | None, int]:
    used: set[int] = set()
    final_proxy = proxy_port or allocate_port(used)
    used.add(final_proxy)
    final_viewer = None
    if need_viewer:
        final_viewer = viewer_port or allocate_port(used)
        used.add(final_viewer)
    final_control = allocate_port(used)
    return final_proxy, final_viewer, final_control
