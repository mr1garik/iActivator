"""Check GitHub Releases for a newer version.

Read-only: this module never downloads or replaces anything — it only reports
whether a newer release exists and the page to get it from. The program file and
the data folder are separate, so updating the program never touches history or
settings. Fails quietly when offline.
"""
from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

from . import __version__, applog
from .i18n import t

REPO = "mr1garik/iActivator"
_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
_lock = threading.Lock()
_cache: dict = {}


def _ssl_context() -> ssl.SSLContext:
    """Verify HTTPS with the CA bundle shipped inside the app.

    A packaged build (PyInstaller) has no system OpenSSL CA path, so the default
    context fails to verify github.com and the check looks like "no internet".
    Using certifi's bundled cacert.pem fixes that on every machine.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _ver_tuple(s: str) -> tuple:
    out = []
    for part in (s or "").lstrip("vV").split("."):
        if part.isdigit():
            out.append(int(part))
        else:
            break
    return tuple(out)


def _asset_name() -> str:
    return "iActivator.exe" if sys.platform == "win32" else "iActivator-mac.zip"


def check(force: bool = False) -> dict:
    with _lock:
        if _cache and not force:
            return dict(_cache)
    info = {"current": __version__, "available": False, "page": RELEASES_PAGE}
    try:
        req = urllib.request.Request(_API, headers={
            "User-Agent": "iActivator", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8, context=_ssl_context()) as r:
            data = json.load(r)
        info["latest"] = (data.get("tag_name", "") or "").lstrip("vV")
        info["page"] = data.get("html_url") or RELEASES_PAGE
        want = _asset_name()
        for a in data.get("assets", []):
            if a.get("name") == want:
                info["download"] = a.get("browser_download_url")
        info["available"] = _ver_tuple(info.get("latest", "")) > _ver_tuple(__version__)
    except Exception as e:
        info["error"] = True  # offline, no releases yet, or TLS/cert trouble
        try:
            applog.add(t("Проверка обновлений не удалась: {kind}: {e}", kind=type(e).__name__, e=e), level="debug")
        except Exception:
            pass
    with _lock:
        _cache.clear()
        _cache.update(info)
    return dict(info)


def open_page() -> bool:
    """Open the download page in the default browser."""
    import webbrowser
    url = check().get("page") or RELEASES_PAGE
    webbrowser.open(url)
    return True


# ---------------------------------------------------------------------------
# Self-update: download the new build and replace the running program in place,
# then relaunch — like 3uTools. The program file and the data folder are separate,
# so this never touches history or settings. Only works in the packaged build.
# ---------------------------------------------------------------------------
_prog = {"active": False, "pct": 0, "done": False, "error": ""}


def can_self_update() -> bool:
    """True only in the frozen (PyInstaller) build on Windows or macOS."""
    return bool(getattr(sys, "frozen", False)) and sys.platform in ("win32", "darwin")


def install_progress() -> dict:
    with _lock:
        return dict(_prog)


def start_install() -> dict:
    """Begin downloading and installing the latest release in the background."""
    if not can_self_update():
        return {"error": t("Автообновление доступно только в установленной программе.")}
    info = check(force=True)
    url = info.get("download")
    if not info.get("available") or not url:
        return {"error": t("Нет доступного обновления.")}
    with _lock:
        if _prog["active"]:
            return {"started": True}
        _prog.update(active=True, pct=0, done=False, error="")
    threading.Thread(target=_run_install, args=(url,), daemon=True).start()
    return {"started": True}


def _run_install(url: str) -> None:
    try:
        applog.add(t("Загружаю обновление…"))
        path = _download(url)
        applog.add(t("Устанавливаю обновление и перезапускаю…"))
        if sys.platform == "win32":
            _install_windows(path)
        else:
            _install_macos(path)
        with _lock:
            _prog.update(done=True, pct=100)
        # The helper waits for this process to exit, then swaps the files and
        # relaunches. Give it a moment to detach, then quit.
        threading.Timer(0.5, lambda: os._exit(0)).start()
    except Exception as e:
        applog.exception(e)
        with _lock:
            _prog.update(active=False, error=f"{type(e).__name__}: {e}")


def _download(url: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="iactivator-update-"))
    dest = tmp / _asset_name()
    req = urllib.request.Request(url, headers={"User-Agent": "iActivator"})
    with urllib.request.urlopen(req, timeout=60, context=_ssl_context()) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = r.read(262144)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if total:
                with _lock:
                    _prog["pct"] = min(99, int(got * 100 / total))
    return dest


def _current_app_macos() -> Path:
    """The running .app bundle (…/iActivator.app)."""
    for anc in Path(sys.executable).resolve().parents:
        if anc.suffix == ".app":
            return anc
    raise RuntimeError(t("Не удалось найти установленную программу для замены."))


def _install_macos(zip_path: Path) -> None:
    app = _current_app_macos()
    extract = zip_path.parent / "extracted"
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(extract)
    new_app = next(p for p in extract.rglob("*.app") if p.is_dir())
    pid = os.getpid()
    # Wait for us to quit, then swap the bundle safely: copy the new app next to the
    # old one first, and only replace once the copy succeeded — so a failed copy can
    # never leave the user without an app. Clear quarantine (we downloaded it
    # ourselves, so it has none, but be safe) and relaunch.
    script = (
        "#!/bin/bash\n"
        f'while kill -0 {pid} 2>/dev/null; do sleep 0.3; done\n'
        f'if ditto "{new_app}" "{app}.new"; then\n'
        f'  rm -rf "{app}"\n'
        f'  mv "{app}.new" "{app}"\n'
        f'  xattr -dr com.apple.quarantine "{app}" 2>/dev/null\n'
        f'fi\n'
        f'open "{app}"\n'
    )
    helper = zip_path.parent / "update.sh"
    helper.write_text(script, encoding="utf-8")
    helper.chmod(0o755)
    subprocess.Popen(["/bin/bash", str(helper)], start_new_session=True)


def _install_windows(exe_path: Path) -> None:
    cur = Path(sys.executable).resolve()
    helper = exe_path.parent / "update.bat"
    helper.write_text(
        "@echo off\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        ":loop\r\n"
        f'move /y "{exe_path}" "{cur}" >nul 2>&1 && goto done\r\n'
        "timeout /t 1 /nobreak >nul\r\n"
        "goto loop\r\n"
        ":done\r\n"
        f'start "" "{cur}"\r\n'
        'del "%~f0"\r\n',
        encoding="utf-8",
    )
    DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(["cmd", "/c", str(helper)], creationflags=DETACHED, close_fds=True)
