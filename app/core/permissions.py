from __future__ import annotations

import ctypes
import os
import subprocess
import sys


def is_admin() -> bool:
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_as_admin(extra_args: list[str] | None = None) -> bool:
    """Ask Windows to relaunch the current program elevated. Returns on UAC denial."""
    if os.name != "nt":
        return False
    executable = sys.executable
    if getattr(sys, "frozen", False):
        parameters = " ".join(_quote(arg) for arg in (extra_args or sys.argv[1:]))
    else:
        script = os.path.abspath(sys.argv[0])
        parameters = " ".join([_quote(script), *(_quote(arg) for arg in (extra_args or sys.argv[1:]))])
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, parameters, None, 1)
    return result > 32


def run_elevated_and_wait(extra_args: list[str]) -> int:
    """Run only a narrowly scoped helper action elevated, then return its exit code."""
    if os.name != "nt":
        raise OSError("Elevação disponível somente no Windows.")
    from win32com.shell import shell, shellcon
    import win32con
    import win32event
    import win32process

    if getattr(sys, "frozen", False):
        executable = sys.executable
        arguments = extra_args
    else:
        executable = sys.executable
        arguments = [os.path.abspath(sys.argv[0]), *extra_args]
    result = shell.ShellExecuteEx(
        fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
        lpVerb="runas",
        lpFile=executable,
        lpParameters=subprocess.list2cmdline(arguments),
        nShow=win32con.SW_HIDE,
    )
    handle = result["hProcess"]
    win32event.WaitForSingleObject(handle, win32event.INFINITE)
    return int(win32process.GetExitCodeProcess(handle))


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'
