from __future__ import annotations

import os
import platform
import socket
import subprocess
from dataclasses import dataclass
from typing import Sequence


CREATE_NO_WINDOW = 0x08000000


@dataclass(slots=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(args: Sequence[str], timeout: int = 30) -> CommandResult:
    """Execute a fixed argument vector without invoking a command shell."""
    completed = subprocess.run(
        list(args), capture_output=True, text=True, encoding="oem", errors="replace",
        timeout=timeout, shell=False, creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    return CommandResult(list(args), completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def computer_name() -> str:
    return socket.gethostname()


def windows_version() -> str:
    return f"{platform.system()} {platform.release()} ({platform.version()})"
