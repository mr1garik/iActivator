"""Windows: check and repair the Apple driver an iPhone needs.

On Windows the program talks to the iPhone through Apple's "Apple Mobile Device
Service" (installed by the Microsoft Store app "Apple Devices" or by iTunes) and the
Apple USB driver (usbaapl64.inf). Three different things break, and each has its own fix:

  1. no Apple software at all          -> install "Apple Devices" from the Microsoft Store
  2. the service is stopped / stuck    -> restart it (needs administrator rights)
  3. Windows sees the iPhone, but not  -> reinstall the Apple USB driver for it
     through Apple's driver (it shows up    (needs administrator rights)
     only as a camera / portable device)

diagnose() is a pure function over the collected facts, so the decisions can be
tested on any system. macOS has the driver built in: nothing to check there.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from .i18n import t

SERVICE = "Apple Mobile Device Service"
_SERVICE_KEY = r"SYSTEM\CurrentControlSet\Services\Apple Mobile Device Service"
MUX_ADDRESS = ("127.0.0.1", 27015)  # where the service listens on Windows
STORE_PRODUCT_ID = "9NP83LWLPZ9K"  # "Apple Devices" in the Microsoft Store (Apple Inc.)
STORE_URL = f"ms-windows-store://pdp/?productid={STORE_PRODUCT_ID}"
STORE_WEB_URL = f"https://apps.microsoft.com/detail/{STORE_PRODUCT_ID.lower()}"
# Apple's USB vendor id; iPhone / iPad / iPod product ids are 0x12xx.
APPLE_MOBILE_PREFIX = "USB\\VID_05AC&PID_12"
_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW: no console flashing on screen


def supported() -> bool:
    return sys.platform == "win32"


# ---------------------------------------------------------------------------
# Facts (Windows only)
# ---------------------------------------------------------------------------
def _service_kind() -> Optional[str]:
    """'store' (Apple Devices), 'itunes', or None when the service is not installed."""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _SERVICE_KEY) as key:
            image_path = str(winreg.QueryValueEx(key, "ImagePath")[0])
    except OSError:
        return None
    return "store" if "windowsapps" in image_path.lower() else "itunes"


def _service_state() -> str:
    """'running', 'stopped' or 'unknown' (sc works without administrator rights)."""
    try:
        out = subprocess.run(["sc", "query", SERVICE], capture_output=True, text=True, timeout=10,
                             creationflags=_NO_WINDOW).stdout
    except Exception:
        return "unknown"
    if "RUNNING" in out:
        return "running"
    if "STOPPED" in out or "STOP_PENDING" in out or "START_PENDING" in out:
        return "stopped"
    return "unknown"


def _mux_reachable() -> bool:
    try:
        with socket.create_connection(MUX_ADDRESS, timeout=1.5):
            return True
    except OSError:
        return False


def _powershell(command: str, timeout: int = 20) -> str:
    script = "[Console]::OutputEncoding = [Text.Encoding]::UTF8\n" + command
    encoded = base64.b64encode(script.encode("utf-16-le")).decode()
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                          capture_output=True, timeout=timeout, creationflags=_NO_WINDOW).stdout.decode("utf-8", "replace")


def _usb_devices() -> Optional[list[dict]]:
    """Apple mobile devices Windows currently sees on USB, with their driver status.
    None when the query itself failed (then nothing can be concluded from it)."""
    try:
        out = _powershell(
            "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like '" + APPLE_MOBILE_PREFIX + "*' } | "
            "Select-Object FriendlyName, Status, Class, InstanceId, @{n='Problem';e={[string]$_.Problem}} | "
            "ConvertTo-Json -Compress")
    except Exception:
        return None
    out = out.strip()
    if not out:
        return []
    try:
        data = json.loads(out)
    except ValueError:
        return None
    rows = data if isinstance(data, list) else [data]
    return [{"name": r.get("FriendlyName") or "", "status": r.get("Status") or "", "class": r.get("Class") or "",
             "id": r.get("InstanceId") or "", "problem": r.get("Problem") or ""} for r in rows]


def collect(mux_devices: Optional[int]) -> dict:
    """Everything diagnose() needs. mux_devices: iPhones the Apple service reports (None if unknown)."""
    if not supported():
        return {"windows": False}
    kind = _service_kind()
    return {
        "windows": True,
        "service": kind,
        "state": _service_state() if kind else "missing",
        "mux": _mux_reachable() if kind else False,
        "mux_devices": mux_devices,
        "usb": _usb_devices(),
    }


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------
def diagnose(f: dict) -> dict:
    """Turn facts into one verdict: level ok|warn|bad, a message, and the fix to offer (or None)."""
    if not f.get("windows"):
        return {"level": "ok", "code": "not_needed", "fix": None,
                "message": t("На этой системе отдельный драйвер не нужен.")}
    kind = f.get("service")
    if not kind:
        return {"level": "bad", "code": "no_driver", "fix": "install",
                "message": t("Драйвер Apple не установлен. Установите приложение «Apple Devices» из Microsoft Store "
                             "(или iTunes), затем перезапустите iActivator.")}
    source = t("Apple Devices из Microsoft Store") if kind == "store" else "iTunes"
    if f.get("state") != "running" or not f.get("mux"):
        return {"level": "bad", "code": "service_stopped", "fix": "restart", "source": source,
                "message": t("Служба Apple ({source}) не отвечает. Перезапустите её — Windows попросит "
                             "разрешение администратора.", source=source)}
    usb = f.get("usb")
    phones = [d for d in (usb or []) if "&MI_" not in d["id"].upper()]  # the device itself, not its USB interfaces
    broken = [d for d in (usb or []) if d["status"] and d["status"].upper() != "OK"]
    if broken:
        return {"level": "bad", "code": "device_driver_error", "fix": "reinstall", "source": source,
                "message": t("Windows видит iPhone, но драйвер работает с ошибкой ({name}: {status}). "
                             "Переустановите драйвер iPhone.", name=broken[0]["name"] or "iPhone",
                             status=broken[0]["problem"] or broken[0]["status"])}
    if phones and f.get("mux_devices") == 0:
        return {"level": "bad", "code": "device_not_seen", "fix": "reinstall", "source": source,
                "message": t("Windows видит iPhone, но служба Apple — нет: у телефона не тот драйвер. "
                             "Переустановите драйвер iPhone.")}
    if phones or (f.get("mux_devices") or 0) > 0:
        return {"level": "ok", "code": "ok", "fix": None, "source": source,
                "message": t("Драйвер Apple работает ({source}), iPhone виден.", source=source)}
    return {"level": "ok", "code": "ok_no_device", "fix": None, "source": source,
            "message": t("Драйвер Apple работает ({source}). Подключите iPhone кабелем и разблокируйте его.",
                         source=source)}


# ---------------------------------------------------------------------------
# Fixes
# ---------------------------------------------------------------------------
def _ps_quote(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


RESTART_SCRIPT = f"""
$n = {_ps_quote(SERVICE)}
Set-Service -Name $n -StartupType Automatic -ErrorAction SilentlyContinue  # a Store-app service may refuse; not needed to restart
Restart-Service -Name $n -Force
Log ('service: ' + (Get-Service -Name $n).Status)
"""

# Finds usbaapl64.inf in the installed Apple package (Store app or iTunes), installs it,
# makes Windows re-detect the connected iPhone with it, and restarts the service.
# Removing the device entry is what "Uninstall device" in Device Manager does: it
# deletes no driver files, the next scan just matches the device again.
REINSTALL_SCRIPT = f"""
$n = {_ps_quote(SERVICE)}
$img = (Get-ItemProperty -Path ('HKLM:\\' + {_ps_quote(_SERVICE_KEY)})).ImagePath
if ($img -match '^\\s*"([^"]+)"') {{ $exe = $Matches[1] }} else {{ $exe = ($img -split '\\.exe')[0] + '.exe' }}
$dir = Split-Path -Parent $exe
$roots = @($dir, (Split-Path -Parent $dir), (Join-Path $env:CommonProgramFiles 'Apple\\Mobile Device Support'))
$inf = $null
foreach ($r in $roots) {{
  if (-not $inf -and $r -and (Test-Path $r)) {{
    $inf = Get-ChildItem -Path $r -Recurse -Filter 'usbaapl64.inf' -ErrorAction SilentlyContinue | Select-Object -First 1
  }}
}}
if (-not $inf) {{ throw 'usbaapl64.inf not found in the Apple package' }}
Log ('driver: ' + $inf.FullName)
Log (pnputil /add-driver $inf.FullName /install | Out-String)
Get-PnpDevice -PresentOnly | Where-Object {{ $_.InstanceId -like {_ps_quote(APPLE_MOBILE_PREFIX + '*')} }} | ForEach-Object {{
  Log (pnputil /remove-device $_.InstanceId | Out-String)
}}
Log (pnputil /scan-devices | Out-String)
Restart-Service -Name $n -Force
Log ('service: ' + (Get-Service -Name $n).Status)
"""


def build_elevated_script(body: str, result_file: Path) -> str:
    """The full script the elevated PowerShell runs; it reports into result_file (UTF-8)."""
    out = _ps_quote(result_file)
    return (
        f"$out = {out}\n"
        "function Log($s) { Add-Content -Path $out -Value ([string]$s).Trim() -Encoding UTF8 }\n"
        "$ErrorActionPreference = 'Stop'\n"
        "try {\n" + body + "\nLog 'RESULT: OK'\n}\n"
        "catch { Log ('RESULT: ERROR ' + $_.Exception.Message) }\n"
    )


def build_launcher(elevated_script: str) -> list[str]:
    """Command that asks Windows for administrator rights (UAC) and runs the script hidden.
    Exit code 5 means the user said no."""
    inner = base64.b64encode(elevated_script.encode("utf-16-le")).decode()
    outer = ("try { Start-Process -FilePath powershell.exe -Verb RunAs -Wait -WindowStyle Hidden "
             f"-ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand','{inner}'; exit 0 }} "
             "catch { exit 5 }")
    return ["powershell", "-NoProfile", "-NonInteractive", "-Command", outer]


def _run_elevated(body: str, timeout: int = 300) -> dict:
    result_file = Path(tempfile.mkdtemp(prefix="iactivator-driver-")) / "result.txt"
    try:
        proc = subprocess.run(build_launcher(build_elevated_script(body, result_file)),
                              timeout=timeout, creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return {"error": t("Windows не завершил операцию вовремя. Перезагрузите компьютер и повторите.")}
    if proc.returncode == 5:
        return {"cancelled": True, "error": t("Нужно разрешение администратора — операция отменена.")}
    try:
        lines = result_file.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        lines = []
    last = next((ln for ln in reversed(lines) if ln.startswith("RESULT:")), "")
    log = [ln for ln in lines if ln and not ln.startswith("RESULT:")]
    if last == "RESULT: OK":
        return {"ok": True, "log": log}
    return {"error": last.replace("RESULT: ERROR", "").strip() or t("Не удалось выполнить операцию."), "log": log}


def open_store() -> dict:
    """Open "Apple Devices" in the Microsoft Store (the user installs it there)."""
    try:
        os.startfile(STORE_URL)  # type: ignore[attr-defined]
    except Exception:
        import webbrowser
        webbrowser.open(STORE_WEB_URL)
    return {"ok": True}


def fix(action: str) -> dict:
    if not supported():
        return {"error": t("Доступно только на Windows.")}
    if action == "install":
        return open_store()
    if action == "restart":
        return _run_elevated(RESTART_SCRIPT, timeout=120)
    if action == "reinstall":
        return _run_elevated(REINSTALL_SCRIPT, timeout=300)
    return {"error": "unknown action"}
