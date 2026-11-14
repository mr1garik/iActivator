"""Check GitHub Releases for a newer version and, in the packaged build, install it.

The program file and the data folder are separate, so updating the program never
touches history or settings. Before the running program is replaced, the download
is verified (size, SHA-256 when GitHub publishes it, and that it really is a
program / a readable archive) and the current version is copied to the data
folder, so a bad download can never leave the user without a working app.
Fails quietly when offline.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
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


# Release file names. Up to v3.0 they were "iActivator.exe" and "iActivator-mac.zip".
# The installer in v3.0 unpacks the Mac archive in a way that loses the executable
# flag and symlinks (the updated app would not start) and may hang on Windows user
# folders with non-Latin names. Releases from v3.1 on use new names, so a v3.0
# install cannot find them and never runs that installer: v3.0 users update once by
# downloading the new version from the releases page.
ASSET_WINDOWS = "iActivator-windows.exe"
ASSET_MACOS = "iActivator-macos.zip"


def _asset_name() -> str:
    return ASSET_WINDOWS if sys.platform == "win32" else ASSET_MACOS


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
                info["size"] = a.get("size")
                info["digest"] = a.get("digest")  # "sha256:…", published by GitHub for newer releases
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
    threading.Thread(target=_run_install, args=(url, info.get("size"), info.get("digest")), daemon=True).start()
    return {"started": True}


def _run_install(url: str, size: int | None = None, digest: str | None = None) -> None:
    try:
        applog.add(t("Загружаю обновление…"))
        path = _download(url)
        _verify_download(path, size, digest)
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
        applog.add(t("❌ Обновление не установлено: {e}. Программа осталась прежней.", e=e))
        with _lock:
            _prog.update(active=False, error=str(e) if isinstance(e, UpdateError) else f"{type(e).__name__}: {e}")


class UpdateError(Exception):
    """A problem with the downloaded update; the message is written for the user."""


# A real build is tens of megabytes; anything smaller is an error page or a cut-off download.
MIN_UPDATE_BYTES = 5 * 1024 * 1024


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
    if total and got != total:
        raise UpdateError(t("Загрузка оборвалась ({got} из {total} байт). Повторите позже.", got=got, total=total))
    return dest


def _verify_download(path: Path, size: int | None, digest: str | None) -> None:
    """Refuse to install anything that is not the complete file from the release."""
    actual = path.stat().st_size
    if size and actual != size:
        raise UpdateError(t("Загрузка оборвалась ({got} из {total} байт). Повторите позже.", got=actual, total=size))
    if actual < MIN_UPDATE_BYTES:
        raise UpdateError(t("Скачанный файл слишком мал и не похож на программу."))
    if digest and digest.lower().startswith("sha256:"):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != digest.split(":", 1)[1].strip().lower():
            raise UpdateError(t("Скачанный файл повреждён (контрольная сумма не совпала)."))
    if path.suffix.lower() == ".exe":
        with open(path, "rb") as f:
            if f.read(2) != b"MZ":
                raise UpdateError(t("Скачанный файл не является программой Windows."))
    else:
        try:
            with zipfile.ZipFile(path) as z:
                broken = z.testzip()
                has_app = any(".app/" in n for n in z.namelist())
        except zipfile.BadZipFile as e:
            raise UpdateError(t("Скачанный архив повреждён.")) from e
        if broken or not has_app:
            raise UpdateError(t("Скачанный архив повреждён."))


def backup_dir() -> Path:
    """Where the previous version is kept after an update (inside the data folder)."""
    from .core import app_data_dir
    d = app_data_dir() / "previous-version"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _current_app_macos() -> Path:
    """The running .app bundle (…/iActivator.app)."""
    for anc in Path(sys.executable).resolve().parents:
        if anc.suffix == ".app":
            return anc
    raise RuntimeError(t("Не удалось найти установленную программу для замены."))


# Paths are passed to the helper scripts as arguments, never written into the script
# text, so names with spaces, quotes or non-Latin letters (a Cyrillic user folder)
# cannot break them.
_MAC_HELPER = r"""#!/bin/bash
# args: pid new_app app backup
PID="$1"; NEW="$2"; APP="$3"; BAK="$4"
while kill -0 "$PID" 2>/dev/null; do sleep 0.3; done
if ditto "$NEW" "$APP.new"; then
  rm -rf "$BAK"
  if mv "$APP" "$BAK" 2>/dev/null || { ditto "$APP" "$BAK" && rm -rf "$APP"; }; then
    if mv "$APP.new" "$APP"; then
      xattr -dr com.apple.quarantine "$APP" 2>/dev/null
    else
      rm -rf "$APP"; mv "$BAK" "$APP" 2>/dev/null || ditto "$BAK" "$APP"   # put the old version back
    fi
  else
    rm -rf "$APP.new"
  fi
else
  rm -rf "$APP.new"
fi
open "$APP"
"""

_WIN_HELPER = (
    "@echo off\r\n"
    "rem args: new_exe current_exe\r\n"
    "setlocal\r\n"
    "set /a N=0\r\n"
    ":wait\r\n"
    "ping -n 2 127.0.0.1 >nul\r\n"            # ~1 s; "timeout" does not work without a console
    'move /y "%~1" "%~2" >nul 2>&1 && goto done\r\n'
    "set /a N+=1\r\n"
    "if %N% lss 60 goto wait\r\n"             # give up after a minute: the old program is still in place
    ":done\r\n"
    'start "" "%~2"\r\n'
    'del "%~f0"\r\n'
)


def _check_extracted_app(folder: Path) -> Path:
    """The unpacked .app bundle, if it can actually start: its main program must be executable."""
    apps = [p for p in folder.glob("*.app") if p.is_dir()] if folder.is_dir() else []
    if not apps:
        raise UpdateError(t("Скачанный архив повреждён."))
    app = apps[0]
    macos = app / "Contents" / "MacOS"
    if not macos.is_dir() or not any(f.is_file() and os.access(f, os.X_OK) for f in macos.iterdir()):
        raise UpdateError(t("Обновление распаковалось неправильно — программа не тронута."))
    return app


def _install_macos(zip_path: Path) -> None:
    app = _current_app_macos()
    extract = zip_path.parent / "extracted"
    # ditto (the tool Finder uses) keeps the executable flags, symlinks and extended
    # attributes an .app bundle needs; Python's zipfile drops all of them.
    subprocess.run(["ditto", "-x", "-k", str(zip_path), str(extract)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    new_app = _check_extracted_app(extract)
    backup = backup_dir() / app.name
    # The helper waits for us to quit, copies the new app next to the old one, moves
    # the old one to the backup folder and only then puts the new one in place; if
    # that last step fails, the old version is moved back.
    helper = zip_path.parent / "update.sh"
    helper.write_text(_MAC_HELPER, encoding="utf-8")
    helper.chmod(0o755)
    applog.add(t("Предыдущая версия будет сохранена в: {path}", path=backup))
    subprocess.Popen(["/bin/bash", str(helper), str(os.getpid()), str(new_app), str(app), str(backup)],
                     start_new_session=True)


def _install_windows(exe_path: Path) -> None:
    cur = Path(sys.executable).resolve()
    backup = backup_dir() / cur.name
    try:
        shutil.copy2(cur, backup)  # a running .exe can be read, so keep the current version first
        applog.add(t("Предыдущая версия сохранена в: {path}", path=backup))
    except OSError as e:
        applog.add(t("⚠ Не удалось сохранить предыдущую версию: {e}", e=e))
    helper = exe_path.parent / "update.bat"
    helper.write_text(_WIN_HELPER, encoding="ascii", newline="")
    DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(["cmd", "/c", str(helper), str(exe_path), str(cur)], creationflags=DETACHED, close_fds=True)
