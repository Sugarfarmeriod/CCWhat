"""Static configuration for deep-ai-analysis."""

from pathlib import Path

# Domains whose HTTP traffic will be recorded.
# Edit this list to add or remove domains.
RECORD_DOMAINS: list[str] = [
    "mcli.sankuai.com",
]

# Default directory for raw HTTP request/response logs (written by `proxy`,
# read by `web-server --req-resp-dir` and `clear-req-resp`).
DEFAULT_RAW_LOG_DIR: Path = Path.home() / ".deep-ai-analysis" / "raw-req-resp"
