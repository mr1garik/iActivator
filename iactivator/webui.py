"""Browser UI: a small local HTTP server (127.0.0.1 only) + one HTML page.

Used instead of Tkinter because the system Tk shipped with macOS is deprecated and
renders blank windows on recent versions; a browser works the same everywhere.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import platform
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__, applog, autostart, core, devicetext, driver, history, i18n, notify, report, settings, tray, update
from .i18n import t

LANGUAGES = [
    ("Украинский", "uk"), ("Русский", "ru"), ("Английский (США)", "en"), ("Английский (Великобритания)", "en-GB"),
    ("Польский", "pl"), ("Немецкий", "de"), ("Французский", "fr"), ("Испанский", "es"), ("Итальянский", "it"),
    ("Португальский (Бразилия)", "pt-BR"), ("Турецкий", "tr"), ("Румынский", "ro"), ("Чешский", "cs"),
    ("Словацкий", "sk"), ("Венгерский", "hu"), ("Казахский", "kk"), ("Иврит", "he"), ("Арабский", "ar"),
    ("Китайский (упрощ.)", "zh-Hans"), ("Китайский (традиц.)", "zh-Hant"), ("Японский", "ja"), ("Корейский", "ko"),
]

REGIONS = [
    ("Украина", "UA", "Europe/Kyiv"), ("Польша", "PL", "Europe/Warsaw"),
    ("Германия", "DE", "Europe/Berlin"), ("Чехия", "CZ", "Europe/Prague"),
    ("Молдова", "MD", "Europe/Chisinau"), ("Румыния", "RO", "Europe/Bucharest"),
    ("Казахстан", "KZ", "Asia/Almaty"), ("Грузия", "GE", "Asia/Tbilisi"),
    ("Турция", "TR", "Europe/Istanbul"), ("Великобритания", "GB", "Europe/London"),
    ("Франция", "FR", "Europe/Paris"), ("Италия", "IT", "Europe/Rome"),
    ("Испания", "ES", "Europe/Madrid"), ("Израиль", "IL", "Asia/Jerusalem"),
    ("ОАЭ", "AE", "Asia/Dubai"), ("США", "US", "America/New_York"),
    ("Канада", "CA", "America/Toronto"), ("Китай", "CN", "Asia/Shanghai"),
]

ACTIVATION = {"Activated": "активирован", "Unactivated": "не активирован"}

# Shown on the About page. Wallets: (coin and network, address).
INSTAGRAM = "https://www.instagram.com/perminov.george"
PANIC_READER = "https://github.com/mr1garik/ios-panic-reader"
REPO = "https://github.com/mr1garik/iActivator"
# Links the About page is allowed to open in the browser via /api/open-url.
OPEN_URL_ALLOWED = {INSTAGRAM, PANIC_READER, REPO}
WALLETS: list[tuple[str, str]] = [("USDT (TRC20)", "TQKtZpsdz7pm9cuXWPE3ZQEboPHva4Uuas")]

PAGE = (Path(__file__).parent / "page.html").read_text(encoding="utf-8")


def _about() -> dict:
    try:
        from importlib.metadata import version
        pmd3 = version("pymobiledevice3")
    except Exception:
        pmd3 = "—"
    return {
        "version": __version__,
        "system": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "pymobiledevice3": pmd3,
        "data_dir": str(core.app_data_dir()),
        "instagram": INSTAGRAM,
        "repo": REPO,
        "wallets": WALLETS,
        "autostart_supported": autostart.supported(),
        "driver_supported": driver.supported(),
        "autostart": autostart.is_enabled(),
    }


def _size(n: int) -> str:
    if n < 1024 * 1024:
        return t("{n} КБ", n=max(1, round(n / 1024)) if n else 0)
    return t("{n} МБ", n=f"{n / 1024 / 1024:.1f}")


def open_url(url: str) -> bool:
    """Open a link in the default browser through the OS, not Python's webbrowser.

    In a packaged build (PyInstaller, and a macOS .app) webbrowser.open often does nothing:
    the frozen app has no console and a minimal environment, so it finds no browser. The
    system opener (`open`, `start`/os.startfile, `xdg-open`) always works. webbrowser stays
    as a last resort."""
    try:
        if sys.platform == "win32":
            import os
            os.startfile(url)  # noqa: S606 - opens the default browser for an http(s) URL
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
        return True
    except Exception:
        try:
            return bool(webbrowser.open(url))
        except Exception:
            return False


def _open_folder(path: str) -> None:
    if sys.platform == "win32":
        import os
        os.startfile(path)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])


class State:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.lock = threading.Lock()
        self.busy = False
        self.current = ""  # serial of the phone the running job works on
        self.queue: list[dict] = []  # phones waiting in auto mode: {"serial", "make"}
        self.labels: dict[str, str] = {}
        self.last_device_error = ""
        self.steps: list[dict] = []  # live activation checklist shown in the UI
        self.applelogin = None  # an owner Apple ID sign-in in progress (core.AppleIDActivation)

    def log(self, msg: str, serial: str = "", level: str = "") -> None:
        applog.add(msg, serial, level)

    def set_steps(self, names: list) -> None:
        self.steps = [{"name": n, "status": "pending", "detail": ""} for n in names]

    def set_step(self, name: str, status: str, detail: str = "") -> None:
        for s in self.steps:
            if s["name"] == name:
                s["status"], s["detail"] = status, detail
                return

    def fail_running_steps(self, detail: str = "") -> None:
        for s in self.steps:
            if s["status"] in ("run", "pending"):
                s["status"], s["detail"] = ("error", detail) if s["status"] == "run" else ("skipped", "")

    def run(self, coro, timeout: float = 120):
        """Run a coroutine on the device loop and wait for its result, at most `timeout` seconds.

        Without a limit, an iPhone or Apple service that stops answering would leave the request
        thread waiting forever, and the window polls every few seconds: threads would pile up.
        On timeout the operation is cancelled (its connection is closed) and an error is raised."""
        fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return fut.result(timeout)
        except concurrent.futures.TimeoutError:
            fut.cancel()
            raise TimeoutError(t("Нет ответа от iPhone или службы Apple за {n} с", n=int(timeout))) from None

    def short_label(self, serial: str) -> str:
        label = self.labels.get(serial, "")
        model = label.split(" · ")[0] if label else "iPhone"
        return f"{model} …{serial[-4:]}" if serial else model

    def run_or_queue(self, make_coro, serial: str) -> int:
        """Start now (returns 0) or put the phone in line (returns its place). A phone already
        running or waiting is not added twice."""
        with self.lock:
            if self.busy:
                if serial == self.current:
                    return -1
                for i, item in enumerate(self.queue, 1):
                    if item["serial"] == serial:
                        return i
                self.queue.append({"serial": serial, "make": make_coro})
                return len(self.queue)
        return 0 if self.run_job(make_coro, serial) else self.run_or_queue(make_coro, serial)

    async def _start_next(self) -> None:
        """After a job: start the next phone in line that is still plugged in."""
        while True:
            with self.lock:
                if not self.queue or self.busy:
                    return
                item = self.queue.pop(0)
            try:
                connected = await core.connected_serials()
            except Exception:
                connected = []
            if item["serial"] not in connected:
                self.log(t("Очередь: {label} отключён — пропускаю", label=self.short_label(item["serial"])),
                         item["serial"], "warn")
                continue
            if not self.run_job(item["make"], item["serial"]):
                with self.lock:
                    self.queue.insert(0, item)  # someone started a job meanwhile; it starts us when done
            return

    def run_job(self, make_coro, serial: str = "") -> bool:
        """Start a long job in the background; its progress goes to the log."""
        with self.lock:
            if self.busy:
                return False
            self.busy = True
            self.current = serial

        async def job():
            try:
                await make_coro()
            except core.UserFacingError as e:
                self.log(f"❌ {e}", serial)
                self.fail_running_steps(str(e))
            except Exception as e:
                self.log(t("❌ Ошибка: ") + core.short_error(e), serial)
                applog.exception(e, serial)
                self.fail_running_steps(core.short_error(e))
            finally:
                with self.lock:
                    self.busy = False
                    self.current = ""
                await self._start_next()
        asyncio.run_coroutine_threadsafe(job(), self.loop)
        return True


STATE = State()


async def _with_activator(serial, fn, action, detail=""):
    act = core.Activator(serial, lambda m: STATE.log(m, serial), step=STATE.set_step)
    STATE.log(t("▶ {action}: {detail}", action=t(action), detail=detail) if detail
              else t("▶ {action}", action=t(action)), serial)
    started = time.monotonic()
    await core.CONNECTIONS.drop(serial)  # the job changes the phone (activation, erase): start clean
    try:
        await fn(act)
        history.add_event(serial, action, "ok", detail)
        STATE.log(t("✅ {action}: готово за {secs} с", action=t(action), secs=f"{time.monotonic() - started:.0f}"), serial)
        notify.phone_done(STATE.short_label(serial), action, True)
    except Exception as e:
        reason = str(e) if isinstance(e, core.UserFacingError) else core.short_error(e)
        history.add_event(serial, action, "error", reason)
        notify.phone_done(STATE.short_label(serial), action, False, reason)
        raise
    finally:
        await act.close()
        await core.CONNECTIONS.drop(serial)


async def _auto_ready(serial: str) -> bool:
    """Auto mode runs only on a phone that still needs activation and is not locked."""
    async with core.device(serial) as lockdown:
        if lockdown.all_values.get("ActivationState") != "Unactivated":
            STATE.log(t("Авто-режим: {label} уже активирован — пропускаю", label=STATE.short_label(serial)), serial)
            return False
        checks = await core.lock_checks(lockdown, core._own_cert(), True)
    bad = [c for c in checks if c["status"] == "bad"]
    if bad:
        reason = f"{bad[0]['name']}: {bad[0]['detail']}"
        STATE.log(t("⛔ Авто-режим остановлен: {reason}", reason=reason), serial, "error")
        history.add_event(serial, "Активация", "error", reason)
        return False
    return True


def _parts_checks(serial: str, parts: dict) -> list:
    """Compare the parts with the first check of this iPhone, then remember any new ones."""
    if "serials" not in parts:
        return []  # diagnostics were not readable (locked iPhone): nothing to say about parts
    baseline, since = history.parts_baseline(serial)
    when = None
    if since:
        try:
            when = datetime.strptime(since, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
        except ValueError:
            when = since
    checks = core.parts_checks(parts["serials"], baseline, when)
    history.record_parts(serial, parts["serials"])
    return checks


def _record_checks(serial: str, action: str, results: list) -> None:
    bad = [r for r in results if r["status"] == "bad"]
    warn = [r for r in results if r["status"] == "warn"]
    for r in results:
        level = {"bad": "error", "warn": "warn", "ok": "ok"}.get(r["status"], "info")
        STATE.log(f"{t(action)} · {r['name']}: {r['detail']}", serial, level if level != "ok" else "debug")
    STATE.log(f"{t(action)}: " + (t("неисправностей {bad}, замечаний {warn}", bad=len(bad), warn=len(warn)) if bad or warn else t("без замечаний")),
              serial, "error" if bad else "warn" if warn else "ok")
    if bad or warn:
        detail = "; ".join(f"{r['name']}: {r['detail']}" for r in bad + warn)
        history.add_event(serial, action, "error" if bad else "warn", detail)
    else:
        history.add_event(serial, action, "ok", t("Без замечаний"))


def _wifi(d: dict):
    if not d.get("ssid"):
        return None
    return core.WifiOptions(
        ssid=d["ssid"],
        password=d.get("password", ""),
        security=d.get("security", "Any"),
        hidden=bool(d.get("hidden")),
        disable_mac_randomization=bool(d.get("nomac", True)),
    )


def _options(d: dict) -> core.SetupOptions:
    return core.SetupOptions(
        language=d.get("language", "uk").strip(),
        region=d.get("region", "UA").strip().upper(),
        timezone=d.get("timezone", "Europe/Kyiv").strip(),
        use_24h=bool(d.get("h24", True)),
        activate=bool(d.get("activate", True)),
        skip_setup=bool(d.get("skip_setup", True)),
        supervise=bool(d.get("supervise", False)),
        organization=(d.get("organization") or "iActivator").strip(),
        wifi=_wifi(d),
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code: int, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8") if isinstance(body, str) \
            else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # the window was reloaded or closed before the answer: nothing to do

    def _after_applelogin(self, res: dict, serial: str = ""):
        """Finish an Apple ID sign-in step: pass a form on to the UI, or, on success, record it
        and drop the sign-in. Credentials are never part of res."""
        if res.get("activated"):
            login, STATE.applelogin = STATE.applelogin, None
            who = serial or (login.serial if login else "")
            if login is not None:
                try:
                    STATE.run(login.close(), timeout=20)
                except Exception:
                    pass
            if who:
                history.add_event(who, "Активация", "ok", t("Вход владельца Apple ID"))
                STATE.log(t("✅ Блокировка активации снята входом владельца."), who, "ok")
        return res

    def _fail(self, e: Exception, serial: str, what: str):
        STATE.log(f"❌ {t(what)}: {core.short_error(e)}", serial)
        applog.exception(e, serial)
        return self._send(200, {"error": core.short_error(e)})

    def _safely(self, handler) -> None:
        """No request may take the server down or leave the window without an answer."""
        try:
            handler()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            applog.exception(e)
            try:
                self._send(500, {"error": core.short_error(e)})
            except Exception:
                pass

    def do_GET(self):
        self._safely(self._do_get)

    def do_POST(self):
        self._safely(self._do_post)

    def _do_get(self):
        if self.path.startswith("/api/labels/preview"):
            # The sticker as it will print, with the saved settings: the latest phone in the
            # history, or a sample phone. Shown in Settings; nothing is saved.
            from . import labels
            try:
                devices = history.summary()["devices"]
                layout = labels.preview(labels.options(settings.load()["ui"]), devices[0] if devices else None)
            except Exception as e:
                applog.exception(e)
                return self._send(200, {"error": t("Не удалось сделать наклейку: {e}", e=core.short_error(e))})
            return self._send(200, layout)
        if self.path == "/api/history":
            return self._send(200, history.summary())
        if self.path == "/api/stats":
            return self._send(200, history.stats_report())
        if self.path == "/api/files/usage":
            u = devicetext.usage()
            return self._send(200, {**u, "size": _size(u["bytes"]), "devices": len(history.export())})
        if self.path == "/":
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if self.path == "/api/meta":
            return self._send(200, {
                "languages": [[t(n), c] for n, c in LANGUAGES], "regions": [[t(n), c, tz] for n, c, tz in REGIONS],
                "security": [[t(k), v] for k, v in core.WIFI_SECURITY.items()],
                "lang": i18n.get_lang(),
                "about": _about(),
            })
        if self.path == "/api/update/progress":
            return self._send(200, update.install_progress())
        if self.path.startswith("/api/update"):
            return self._send(200, update.status(force="force" in self.path))
        if self.path.startswith("/api/log"):
            entries, total = applog.since(int(self.path.partition("since=")[2] or 0))
            steps = [{**s, "name": t(s["name"]), "detail": t(s["detail"])} for s in STATE.steps]
            with STATE.lock:
                current = STATE.short_label(STATE.current) if STATE.busy and STATE.current else ""
                waiting = [STATE.short_label(q["serial"]) for q in STATE.queue]
            return self._send(200, {"entries": entries, "next": total, "busy": STATE.busy, "steps": steps,
                                    "current": current, "queue": waiting})
        if self.path == "/api/driver":
            return self._send(200, _driver_status())
        if self.path.startswith("/api/devices"):
            # Polled every few seconds: cheap usbmux listing, full labels only for new devices
            # or when the page asks for a refresh.
            try:
                serials = STATE.run(core.connected_serials(), timeout=10)
                if "full=1" in self.path or any(s not in STATE.labels for s in serials):
                    STATE.labels = {d.serial: d.label() for d in STATE.run(core.list_devices(), timeout=30)}
                STATE.last_device_error = ""
                return self._send(200, [{"serial": s, "label": STATE.labels.get(s, s)} for s in serials])
            except Exception as e:
                msg = t("Не удалось получить список устройств: {e}", e=core.short_error(e))
                if msg != STATE.last_device_error:  # polled every 3 s: log a failure once, not every time
                    STATE.log("⚠ " + msg)
                    applog.exception(e)
                STATE.last_device_error = msg
                return self._send(200, {"error": msg})
        self._send(404, {"error": "not found"})

    def _do_post(self):
        # Only accept requests from our own page (blocks other websites from poking the API).
        if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{self.server.server_port}"):
            return self._send(403, {"error": "forbidden"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(d, dict):
                raise ValueError("not an object")
        except ValueError:
            return self._send(400, {"error": "bad request"})

        if self.path == "/api/settings":
            return self._send(200, settings.load())
        if self.path == "/api/network/password":
            return self._send(200, {"password": settings.get_password(d.get("ssid", ""))})
        if self.path == "/api/network/save":
            if not d.get("ssid", "").strip():
                return self._send(400, {"error": t("Введите имя сети")})
            settings.save_network(d["ssid"], d.get("password", ""), d.get("security", "Any"),
                                  bool(d.get("hidden")), bool(d.get("nomac", True)))
            STATE.log(t("Сеть «{ssid}» сохранена (защита {security}{hidden})", ssid=d['ssid'].strip(),
                        security=d.get('security', 'Any'), hidden=(t(", скрытая") if d.get("hidden") else "")))
            return self._send(200, settings.load())
        if self.path == "/api/network/delete":
            settings.delete_network(d.get("ssid", ""))
            STATE.log(t("Сеть «{ssid}» удалена", ssid=d.get('ssid', '')))
            return self._send(200, settings.load())
        if self.path == "/api/settings/autostart":
            on = autostart.set_enabled(bool(d.get("on")))
            STATE.log(t("Автозапуск с Windows: {state}", state=t("включён") if on else t("выключен")))
            return self._send(200, {"autostart": on})
        if self.path == "/api/settings/ui":
            settings.save_ui(d)
            if "cleanup_days" in d:
                threading.Thread(target=_auto_cleanup, daemon=True).start()
            if d.get("lang") in settings.LANGS:
                i18n.set_lang(d["lang"])
            if d.get("theme"):
                STATE.log(t("Тема оформления: {theme}", theme=t(THEME_NAMES.get(d.get("theme"), d.get("theme")))), level="debug")
            return self._send(200, settings.load())
        if self.path == "/api/settings/export":
            return self._send(200, _export(bool(d.get("secrets")), bool(d.get("history"))))
        if self.path == "/api/settings/import":
            try:
                done = settings.import_data(d.get("data"))
            except Exception as e:
                STATE.log(t("❌ Импорт настроек: {e}", e=e))
                return self._send(200, {"error": t("Не удалось загрузить настройки: {e}", e=e)})
            STATE.log(t("✅ Настройки загружены из «{name}»", name=d.get('name') or t("файла")))
            for line in done:
                STATE.log("  " + line, level="warn" if line.startswith("⚠") else "info")
            return self._send(200, {"done": done})
        if self.path == "/api/journal":
            # Messages the page writes itself (device unplugged, auto mode, …)
            STATE.log(str(d.get("text", ""))[:500], str(d.get("serial") or ""), d.get("level", ""))
            return self._send(200, {"ok": True})
        if self.path == "/api/logs/open":
            _open_folder(str(applog.logs_dir()))
            return self._send(200, {"ok": True})
        if self.path == "/api/logs/export":
            return self._send(200, _export_logs(bool(d.get("history", True)), bool(d.get("redact"))))
        if self.path == "/api/driver/fix":
            action = d.get("action", "")
            with STATE.lock:
                if STATE.busy:
                    return self._send(409, {"error": t("Уже выполняется другая операция")})
                STATE.busy = True  # no activation while the driver is being replaced
            try:
                STATE.log(t("Драйвер Apple: {action}…", action=t(DRIVER_ACTIONS.get(action, action))))
                res = driver.fix(action)
            finally:
                STATE.busy = False
            if res.get("ok"):
                STATE.log(t("✅ Драйвер Apple: {action} — готово", action=t(DRIVER_ACTIONS.get(action, action))), level="ok")
            elif res.get("error"):
                STATE.log(t("❌ Драйвер Apple: {e}", e=res["error"]))
            for line in res.get("log", []):
                STATE.log("  " + line, level="debug")
            if action in ("restart", "reinstall"):
                STATE.labels = {}  # re-read device names once the driver is back
            return self._send(200, res)
        if self.path == "/api/open-url":
            url = d.get("url", "")
            if url in OPEN_URL_ALLOWED:
                if not open_url(url):
                    return self._send(200, {"error": t("Не удалось открыть браузер. Ссылка: {url}", url=url), "url": url})
            return self._send(200, {"ok": True})
        if self.path == "/api/update/open":
            update.open_page()
            return self._send(200, {"ok": True})
        if self.path == "/api/update/install":
            return self._send(200, update.start_install())

        if self.path == "/api/open-data":
            _open_folder(str(core.app_data_dir()))
            return self._send(200, {"ok": True})

        if self.path == "/api/history/open":
            history.flush_csv()
            _open_folder(str(history.csv_path() if history.csv_path().exists() else core.app_data_dir()))
            return self._send(200, {"ok": True})
        if self.path == "/api/reports/open":
            _open_folder(str(report.reports_dir()))
            return self._send(200, {"ok": True})
        if self.path == "/api/history/txt":
            # One phone: write its file and open it. All phones: write every file, open the folder.
            ids = None if d.get("all") else [d.get("serial", "")]
            paths = devicetext.save(ids)
            if not paths:
                return self._send(200, {"error": t("Этого устройства нет в истории.")})
            _open_folder(str(paths[0] if ids else devicetext.texts_dir()))
            applog.add(t("TXT-файлы сохранены: {n}", n=len(paths)))
            return self._send(200, {"ok": True, "saved": len(paths)})
        if self.path == "/api/files/clear":
            r = devicetext.clear_all()
            applog.add(t("История очищена: устройств {d}, файлов {n}, освобождено {size}",
                         d=r["devices"], n=r["removed"], size=_size(r["bytes"])))
            return self._send(200, {**r, "size": _size(r["bytes"])})
        if self.path == "/api/labels":
            from . import labels
            opts = labels.options(settings.load()["ui"])
            ids = [str(i) for i in (d.get("ids") or [])][:2000]
            if len(ids) == 1 and labels.custom_lines(d.get("lines")):
                opts["custom"] = labels.custom_lines(d.get("lines"))  # edited before printing
            try:
                path = labels.make(ids, opts)
            except Exception as e:
                applog.exception(e)
                return self._send(200, {"error": t("Не удалось сделать наклейку: {e}", e=core.short_error(e))})
            if path is None:
                return self._send(200, {"error": t("Этого устройства нет в истории.")})
            if len(ids) == 1:
                history.add_event(ids[0], "Наклейка", "info", path.name)
            STATE.log(t("🏷 Наклейки сохранены: {n} · {name}", n=len(ids), name=path.name))
            return self._send(200, {"ok": True, "path": str(path)})
        if self.path in ("/api/labels/edit", "/api/labels/preview"):
            # The sticker dialog: /edit gives the template's lines for one phone (to edit),
            # /preview lays out the sticker with the edited lines. Nothing is saved.
            from . import labels
            opts = labels.options(settings.load()["ui"])
            device = history.export().get(str(d.get("id") or ""))
            if device is None:
                return self._send(200, {"error": t("Этого устройства нет в истории.")})
            if self.path == "/api/labels/edit":
                return self._send(200, {"lines": [{"text": x, "bold": b} for x, b in labels.lines_for(device, opts)]})
            custom = labels.custom_lines(d.get("lines"))
            try:
                return self._send(200, labels.preview({**opts, "custom": custom} if custom else opts, device,
                                                      example_note=False))
            except Exception as e:
                applog.exception(e)
                return self._send(200, {"error": t("Не удалось сделать наклейку: {e}", e=core.short_error(e))})
        if self.path == "/api/history/note":
            if not history.set_note(d.get("serial", ""), str(d.get("note") or "")):
                return self._send(200, {"error": t("Этого устройства нет в истории.")})
            return self._send(200, {"ok": True})
        if self.path == "/api/history/delete":
            history.delete(d.get("serial", ""))
            return self._send(200, {"ok": True})

        if self.path == "/api/settings/last":
            settings.save_last(d)
            return self._send(200, {"ok": True})
        if self.path == "/api/preset/save":
            name = settings.save_preset(d.get("name", ""), d.get("values") or {})
            if not name:
                return self._send(200, {"error": t("Введите название профиля.")})
            STATE.log(t("Профиль сохранён: {name}", name=name))
            return self._send(200, {"ok": True, "presets": settings.load()["presets"]})
        if self.path == "/api/preset/delete":
            settings.delete_preset(d.get("name", ""))
            return self._send(200, {"ok": True, "presets": settings.load()["presets"]})

        # Owner Apple ID sign-in for Activation Lock. The values (Apple ID, password, a 2FA code)
        # are forwarded straight to Apple and never logged or stored.
        if self.path == "/api/activation/applelogin/submit":
            login = STATE.applelogin
            if login is None:
                return self._send(200, {"error": t("Вход прерван. Начните заново.")})
            try:
                res = STATE.run(login.submit(d.get("values") or {}), timeout=120)
            except Exception as e:
                return self._send(200, {"error": core.short_error(e)})
            return self._send(200, self._after_applelogin(res))
        if self.path == "/api/activation/applelogin/cancel":
            login, STATE.applelogin = STATE.applelogin, None
            if login is not None:
                try:
                    STATE.run(login.close(), timeout=20)
                except Exception:
                    pass
            return self._send(200, {"ok": True})

        serial = d.get("serial")
        if not serial:
            return self._send(400, {"error": t("Не выбрано устройство")})

        if self.path == "/api/activation/applelogin/start":
            if STATE.busy:
                return self._send(200, {"error": t("Дождитесь окончания текущей операции.")})
            old, STATE.applelogin = STATE.applelogin, None
            if old is not None:
                try:
                    STATE.run(old.close(), timeout=20)
                except Exception:
                    pass
            login = core.AppleIDActivation(serial, lambda m: STATE.log(m, serial))
            STATE.log(t("Вход владельца Apple ID для снятия блокировки активации…"), serial)
            try:
                res = STATE.run(login.start(), timeout=120)
            except Exception as e:
                try:
                    STATE.run(login.close(), timeout=10)
                except Exception:
                    pass
                return self._fail(e, serial, "Вход Apple ID")
            STATE.applelogin = login
            return self._send(200, self._after_applelogin(res, serial))

        if self.path == "/api/locks":
            try:
                res = STATE.run(core.get_lock_checks(serial, check_activation=not STATE.busy))
                if d.get("record"):
                    _record_checks(serial, "Локатор и MDM", res)
                return self._send(200, res)
            except Exception as e:
                return self._fail(e, serial, "Локатор и MDM")

        if self.path == "/api/check":
            STATE.log("Диагностика: проверяю…", serial)
            try:
                parts: dict = {}
                res = STATE.run(core.run_health_check(serial, check_activation=not STATE.busy, parts_out=parts), timeout=180)
                res += _parts_checks(serial, parts)
                _record_checks(serial, "Диагностика", res)
                return self._send(200, res)
            except Exception as e:
                return self._fail(e, serial, "Диагностика")

        if self.path == "/api/report":
            try:
                info = STATE.run(core.get_device_details(serial))
                history.update_device(info)
                parts = {}
                results = STATE.run(core.run_health_check(serial, check_activation=not STATE.busy, parts_out=parts), timeout=180)
                results += _parts_checks(serial, parts)
                _record_checks(serial, "Диагностика", results)
                info["note"] = history.note(serial)
                path = report.build_pdf(info, results, STATE.steps, lang=i18n.get_lang())
                history.add_event(serial, "PDF-отчёт", "info", path.name)
                STATE.log(t("📄 Отчёт сохранён: {path}", path=path), serial, "ok")
                report.open_file(path)
                return self._send(200, {"path": str(path)})
            except Exception as e:
                return self._fail(e, serial, "PDF-отчёт")

        if self.path in ("/api/run", "/api/wifi"):
            # Remember the form (and the network, if asked) before the job starts.
            try:
                settings.save_last(d)
                if d.get("ssid", "").strip():
                    settings.save_network(d["ssid"], d.get("password", ""), d.get("security", "Any"),
                                          bool(d.get("hidden")), bool(d.get("nomac", True)))
            except Exception as e:
                STATE.log(t("⚠ Не удалось сохранить сеть: {e}", e=e), serial)

        if self.path == "/api/languages":
            try:
                langs, _ = STATE.run(core.get_supported_languages(serial))
                return self._send(200, langs)
            except Exception as e:
                return self._fail(e, serial, "Языки устройства")

        if self.path == "/api/info":
            try:
                info = STATE.run(core.get_device_details(serial))
                history.update_device(info)
                if d.get("record"):
                    b = info.get("battery") or {}
                    detail = (f"{t(ACTIVATION.get(info.get('activation'), info.get('activation')) or '')}, iOS {info.get('ios')} ({info.get('build')})"
                              + (t(", батарея {h}%", h=min(b["health"], 100)) if b.get("health") is not None else ""))
                    history.add_event(serial, "Подключение", "info", detail)
                    STATE.log(t("Подключён {model}", model=t(info.get("model_name") or "iPhone"))
                              + (f", {info['capacity']}" if info.get("capacity") else "") + f": {detail}", serial)
                    STATE.log(f"IMEI {info.get('imei') or '—'}" + (f", IMEI 2 {info['imei2']}" if info.get("imei2") else ""),
                              serial, "debug")
                return self._send(200, info)
            except Exception as e:
                return self._fail(e, serial, "Чтение данных")

        if self.path == "/api/run":
            opts = _options(d)
            detail = f"{opts.language}, {opts.region}" + (f", Wi-Fi «{opts.wifi.ssid}»" if opts.wifi else "")
            action = "Активация" if opts.activate else "Настройка"
            names = ([core.STEP_ACTIVATE] if opts.activate else []) + [core.STEP_LANG]
            names += [core.STEP_SKIP] if opts.skip_setup else []
            names += [core.STEP_WIFI] if opts.wifi else []

            async def job():
                STATE.set_steps(names)  # only once it really starts, not while another phone runs
                if d.get("queue") and not await _auto_ready(serial):
                    STATE.set_steps([])
                    return
                await _with_activator(serial, lambda a: a.run(opts), action, detail)
            if d.get("queue"):  # auto mode: several phones are handled one after another
                place = STATE.run_or_queue(job, serial)
                if place > 0:
                    STATE.log(t("Авто-режим: {label} — в очереди ({n})", label=STATE.short_label(serial), n=place), serial)
                return self._send(200, {"ok": True, "queued": max(place, 0)})
        elif self.path == "/api/wifi":
            wifi = _wifi(d)
            if wifi is None:
                return self._send(400, {"error": t("Введите имя сети")})

            async def job():
                STATE.set_steps([])
                await _with_activator(serial, lambda a: a.install_wifi_only(wifi), "Wi-Fi", f"«{wifi.ssid}»")
        elif self.path == "/api/erase":

            async def job():
                STATE.set_steps([])
                await _with_activator(serial, lambda a: a.erase(), "Стирание")
        else:
            return self._send(404, {"error": "not found"})
        if not STATE.run_job(job, serial):
            return self._send(409, {"error": t("Уже выполняется другая операция")})
        self._send(200, {"ok": True})


DRIVER_ACTIONS = {"install": "установка Apple Devices", "restart": "перезапуск службы",
                  "reinstall": "переустановка драйвера iPhone"}


def _driver_status() -> dict:
    """Check the Apple driver (Windows). The service's own device count tells a working
    driver from an iPhone Windows sees only as a camera."""
    mux_devices = None
    if driver.supported():
        try:
            mux_devices = len(STATE.run(core.connected_serials(), timeout=10))
        except Exception:
            mux_devices = None
    facts = driver.collect(mux_devices)
    verdict = driver.diagnose(facts)
    STATE.log(t("Драйвер Apple: {message}", message=verdict["message"]),
              level={"ok": "debug", "warn": "warn", "bad": "warn"}[verdict["level"]])
    return {"supported": driver.supported(), **verdict, "facts": facts}


THEME_NAMES = {"auto": "как в системе", "light": "светлая", "dark": "тёмная",
               "night": "синяя ночь", "mint": "мятная", "graphite": "графит"}
WINDOW = None  # pywebview window, for native file dialogs


def _save_path(name: str):
    """Ask where to save a file; without the native window, use Downloads."""
    if WINDOW is None:
        folder = Path.home() / "Downloads"
        return (folder if folder.is_dir() else core.app_data_dir()) / name
    import webview
    kind = webview.FileDialog.SAVE if hasattr(webview, "FileDialog") else webview.SAVE_DIALOG
    res = WINDOW.create_file_dialog(kind, save_filename=name)
    if not res:
        return None
    return Path(res if isinstance(res, str) else res[0])


def _export(secrets: bool, with_history: bool) -> dict:
    path = _save_path(t("iActivator-настройки-{date}.json", date=time.strftime("%Y-%m-%d")))
    if path is None:
        return {"cancelled": True}
    data = settings.export_data(secrets, with_history)
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        STATE.log(t("❌ Не удалось сохранить настройки: {e}", e=e))
        return {"error": t("Не удалось сохранить файл: {e}", e=e)}
    STATE.log(t("✅ Настройки сохранены в файл: {path}", path=path))
    STATE.log(t("  Сети Wi-Fi: {n}", n=len(data["networks"])) + t(", с паролями" if secrets else ", без паролей")
              + (t(", ключ контролируемого режима") if "supervision_keybag" in data else "")
              + (t(", история: устройств {n}", n=len(data['history'])) if "history" in data else ""))
    if WINDOW is None:
        _open_folder(str(path.parent))
    return {"path": str(path)}


def _device_identifiers() -> set:
    """Every serial number / IMEI / UDID the program knows, to blank out when sharing."""
    ids: set = set()
    try:
        for key, d in history.export().items():
            ids.add(str(key))
            for k in ("id", "serial", "imei", "imei2"):
                if d.get(k):
                    ids.add(str(d[k]))
    except Exception:
        pass
    return {i for i in ids if i and i != "-" and len(i) >= 5}


def _redact_ids(text: str, idents: set) -> str:
    """Replace known identifiers, then IMEI-like digit runs and UDIDs, with ***."""
    for ident in sorted(idents, key=len, reverse=True):
        text = text.replace(ident, "***")
    text = re.sub(r"\b\d{14,15}\b", "***", text)                       # IMEI
    text = re.sub(r"\b89\d{16,20}F?\b", "***", text)                   # ICCID (SIM card number)
    text = re.sub(r"\b[0-9a-fA-F]{40}\b", "***", text)                 # old-style UDID
    text = re.sub(r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16}\b", "***", text)  # new-style UDID
    return text


def _export_logs(with_history: bool, redact: bool = False) -> dict:
    """Bundle the daily logs (and optionally the device history) into one text file
    that can be sent for support/diagnosis. With redact=True the serial numbers and
    IMEIs are blanked out and the history is left out, so the file can be shared
    without revealing which devices were processed."""
    if redact:
        with_history = False
    suffix = t("-без-номеров") if redact else ""
    path = _save_path(t("iActivator-журнал{suffix}-{date}.txt", suffix=suffix, date=time.strftime("%Y-%m-%d_%H%M")))
    if path is None:
        return {"cancelled": True}
    a = _about()
    parts = [
        t("=== iActivator — журнал для диагностики ==="),
        t("Создан: {when}", when=time.strftime("%Y-%m-%d %H:%M:%S")),
        t("Версия: {v}   Система: {sys}   Python: {py}   pymobiledevice3: {pmd}",
          v=a["version"], sys=a["system"], py=a["python"], pmd=a["pymobiledevice3"]),
    ]
    if redact:
        parts.append(t("Серийные номера, IMEI и UDID скрыты (***); история устройств не включена."))
    parts.append("")
    logs = sorted(applog.logs_dir().glob("*.log"))
    if logs:
        parts.append(t("=== ЗАПИСИ ЖУРНАЛА (файлов: {n}) ===", n=len(logs)))
        for p in logs:
            try:
                parts.append(f"\n----- {p.name} -----\n" + p.read_text(encoding="utf-8").rstrip())
            except OSError as e:
                parts.append(f"\n----- {p.name} ----- " + t("(не удалось прочитать: {e})", e=e))
    else:
        parts.append(t("=== ЗАПИСЕЙ ЖУРНАЛА ПОКА НЕТ ==="))
    if with_history:
        parts.append("\n\n" + t("=== ИСТОРИЯ УСТРОЙСТВ (JSON) ==="))
        parts.append(json.dumps(history.export(), ensure_ascii=False, indent=1))
    text = "\n".join(parts) + "\n"
    if redact:
        text = _redact_ids(text, _device_identifiers())
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as e:
        STATE.log(t("❌ Не удалось сохранить журнал: {e}", e=e))
        return {"error": t("Не удалось сохранить файл: {e}", e=e)}
    STATE.log(t("✅ Журнал сохранён в файл: {path}", path=path))
    if WINDOW is None:
        _open_folder(str(path.parent))
    return {"path": str(path)}


def _free_port(preferred: int = 8765) -> int:
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # same as the server, so a restart keeps the port
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


DEFAULT_W, DEFAULT_H = 1120, 780
MIN_W, MIN_H = 640, 560


def _window_geometry(webview):
    """Size and place the window so it always fits the screen, reusing the last size
    the user left when it still fits. Without this the fixed 1120x780 window opens
    bigger than the screen on Windows laptops scaled to 125-150%, pushing the bottom
    bar and corners off-screen."""
    try:
        scr = webview.screens[0]
        sw, sh = int(scr.width), int(scr.height)
    except Exception:
        sw, sh = DEFAULT_W, DEFAULT_H  # screen size unknown: fall back to the design size
    fit_w, fit_h = min(DEFAULT_W, int(sw * 0.92)), min(DEFAULT_H, int(sh * 0.90))
    saved = settings.get_window()
    w = saved["w"] if isinstance(saved.get("w"), int) else fit_w
    h = saved["h"] if isinstance(saved.get("h"), int) else fit_h
    w = max(MIN_W, min(w, sw))  # never wider/taller than the actual screen
    h = max(MIN_H, min(h, sh))
    if isinstance(saved.get("x"), int) and isinstance(saved.get("y"), int) \
            and 0 <= saved["x"] <= sw - w and 0 <= saved["y"] <= sh - h:
        x, y = saved["x"], saved["y"]
    else:  # center it, biased slightly up so it clears the taskbar/dock
        x, y = max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 10)
    min_size = (min(MIN_W, w), min(MIN_H, h))  # min_size must not exceed the window itself
    return w, h, x, y, min_size


def _auto_cleanup() -> None:
    try:
        days = settings.load()["ui"].get("cleanup_days", 0)
        r = devicetext.cleanup(days)
        if r["devices"] or r["removed"]:
            STATE.log(t("Автоочистка (старше {days} дн.): устройств {d}, файлов {n}, освобождено {size}",
                        days=days, d=r["devices"], n=r["removed"], size=_size(r["bytes"])))
    except Exception as e:
        applog.exception(e)


def _start_auto_cleanup() -> None:
    """At start and then every 6 hours (the app may stay open for days)."""
    def loop():
        while True:
            _auto_cleanup()
            time.sleep(6 * 3600)
    threading.Thread(target=loop, daemon=True).start()


def main():
    # Trim Edge WebView2 (Chromium) memory on Windows: no GPU process, smaller JS heap.
    # Must be set before the WebView2 environment starts. Harmless on macOS (WebKit).
    if sys.platform == "win32":
        import os
        os.environ.setdefault("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",
                              "--disable-gpu --disable-dev-shm-usage --js-flags=--max-old-space-size=128")

    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    try:
        import webview  # native window: WebKit on macOS, Edge WebView2 on Windows
    except ImportError:
        webview = None

    applog.cleanup()
    try:
        if autostart.repair():
            STATE.log("Автозапуск: путь к программе обновлён", level="debug")
    except Exception:
        pass  # never block the start over the start-up entry
    i18n.set_lang(settings.load()["ui"].get("lang", "ru"))
    _start_auto_cleanup()
    STATE.log(t("iActivator {v} запущен · {sys} · Python {py}", v=__version__,
                sys=f"{platform.system()} {platform.release()}", py=platform.python_version()),
              level="debug")

    if webview is not None:
        global WINDOW
        threading.Thread(target=server.serve_forever, daemon=True).start()
        w, h, x, y, min_size = _window_geometry(webview)
        WINDOW = webview.create_window(f"iActivator {__version__}", url, width=w, height=h,
                                       x=x, y=y, min_size=min_size)
        # Remember where the user left the window; write once on close, not on every drag.
        geom: dict = {}
        WINDOW.events.resized += lambda width, height: geom.update(w=width, h=height)
        WINDOW.events.moved += lambda nx, ny: geom.update(x=nx, y=ny)

        def _on_closing():
            settings.save_window(geom)
            return tray.on_closing(WINDOW)  # on Windows: hide to tray instead of quitting

        WINDOW.events.closing += _on_closing

        if sys.platform == "win32":
            tray.start_windows_tray(WINDOW)
            webview.start()
        else:
            webview.start(menu=tray.mac_menu(WINDOW))  # macOS menu bar
        return

    # Fallback without pywebview: open the page in the default browser.
    print(f"iActivator открыт в браузере: {url}")
    print("Не закрывайте это окно, пока работаете с программой. Выход: Ctrl+C.")
    threading.Timer(0.5, lambda: open_url(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
