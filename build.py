"""Build iActivator with PyInstaller — one place for the options used by the GitHub
workflow, build_windows.bat and build_mac.sh.

    python build.py

Windows: dist/iActivator.exe (one file).  macOS: dist/iActivator.app.

Why the exclusions: pymobiledevice3 brings in the dependencies of its command-line
tools (an IPython shell, screen streaming with PyAV, the iOS 17+ network tunnel, firmware
and backup parsers, a web server). This app uses only the USB lockdown services
(activation, configuration profiles, diagnostics, crash logs), which import none of
them, but `--collect-all pymobiledevice3` would pack them all: over 150 MB, which the
one-file Windows build unpacks to a temporary folder on every start (and antivirus
scans it), so the app started slowly. tests/test_build.py checks that the app's own
imports never need an excluded package.
"""
from __future__ import annotations

import sys

# Packages the app never imports (checked against what it loads at run time).
EXCLUDES = [
    # IPython shell of the pymobiledevice3 CLI, and what only it needs
    "IPython", "jedi", "parso", "matplotlib_inline", "stack_data", "executing", "asttokens",
    "pure_eval", "traitlets", "pexpect", "ptyprocess",
    # screen streaming (PyAV is >100 MB with its libraries)
    "av",
    # iOS 17+ remote tunnel / QUIC / network stack
    "qh3", "pmd_pytcp", "pmd_net_proto", "pytun_pmd3", "sslpsk_pmd3",
    # firmware, disk image, backup and trace parsers
    "ipsw_parser", "developer_disk_image", "pyimg4", "pyiosbackup", "remotezip", "apple_compress",
    "opack2", "pcapng", "pykdebugparser", "bpylist2", "gifs",
    # web servers used by some CLI commands
    "fastapi", "uvicorn", "starlette", "pydantic", "pydantic_core", "asgiwebdav",
    # crypto library used only by the parts above (the app uses `cryptography`)
    "Crypto",
    # GUI toolkit we don't use
    "tkinter",
]


def pyinstaller_args(entry: str = "main.py", name: str = "iActivator", excludes: bool = True,
                     platform: str = sys.platform) -> list[str]:
    sep = ";" if platform == "win32" else ":"
    args = ["--noconfirm", "--windowed", "--name", name,
            "--collect-all", "pymobiledevice3", "--collect-all", "webview",
            "--collect-submodules", "keyring", "--collect-data", "fpdf",
            "--add-data", f"iactivator/page.html{sep}iactivator"]
    if platform == "win32":
        args += ["--onefile", "--icon", "assets/icon.ico", "--collect-submodules", "pystray",
                 "--collect-submodules", "PIL"]
    elif platform == "darwin":
        args += ["--icon", "assets/icon.icns"]
    else:
        args += ["--onefile"]  # only for trying the build on Linux
    if excludes:
        for module in EXCLUDES:
            args += ["--exclude-module", module]
    return args + [entry]


def main() -> None:
    import PyInstaller.__main__
    PyInstaller.__main__.run(pyinstaller_args())


if __name__ == "__main__":
    main()
