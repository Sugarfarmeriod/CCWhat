from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class AnalyzerSpec:
    name: str
    default_command: list[str]
    output_mode: str  # stdout | jsonl_text | last_message_file
    experimental: bool = False
    timeout_seconds: int = 120
    parse_output: Callable[[str, str, dict[str, str]], str] | None = None

    def parse(self, stdout: str, stderr: str = "", extra_files: dict[str, str] | None = None) -> str:
        if self.parse_output:
            return self.parse_output(stdout, stderr, extra_files or {})
        return stdout.strip()
