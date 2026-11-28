"""Single-instance guard.

Without this, launching iActivator a second time (desktop shortcut, autostart,
the self-updater, or a double click while the window is hidden in the tray)
spawns another process and another tray icon, so several copies pile up.

The first instance binds a fixed loopback port and listens on it. A later
instance fails to bind, connects to that port, hands over a magic token, and —
once the running copy confirms by bringing its window to the front — exits.
If the port is held by something unrelated (handshake not confirmed), we do
NOT block startup: better a rare second window than a program that won't open.
"""
from __future__ import annotations

import socket
import threading

HOST = "127.0.0.1"
# Fixed, app-specific loopback port for the instance handshake.
PORT = 49217
_MAGIC = b"iActivator-show\n"
_ACK = b"ok\n"
_TIMEOUT = 1.5

_sock: socket.socket | None = None  # kept referenced so it stays bound for the process life


def _recv_exact(conn: socket.socket, n: int) -> bytes:
    """Read exactly n bytes. TCP is a stream, so a single recv() may return fewer
    bytes than asked; keep reading until we have them all (or the peer closes)."""
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            break  # peer closed early
        buf += chunk
    return buf


def _ping_primary() -> bool:
    """Ask an already-running instance to show itself. True only if one answered."""
    try:
        with socket.create_connection((HOST, PORT), timeout=_TIMEOUT) as c:
            c.settimeout(_TIMEOUT)
            c.sendall(_MAGIC)
            return _recv_exact(c, len(_ACK)) == _ACK
    except OSError:
        return False


def _serve(sock: socket.socket, on_show) -> None:
    def loop():
        while True:
            try:
                conn, _ = sock.accept()
            except OSError:
                return  # socket closed on quit
            with conn:
                try:
                    conn.settimeout(_TIMEOUT)
                    if _recv_exact(conn, len(_MAGIC)) == _MAGIC:
                        conn.sendall(_ACK)
                        try:
                            on_show()
                        except Exception:
                            pass
                except OSError:
                    pass

    threading.Thread(target=loop, daemon=True).start()


def acquire(on_show) -> bool:
    """Become the single instance.

    Returns True if this process should keep starting (it is the primary, or the
    lock port is taken by something that is not us). Returns False if another
    iActivator is already running — it was brought to the front and this process
    should exit quietly.
    """
    global _sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Deliberately NOT SO_REUSEADDR/SO_REUSEPORT: the whole guard relies on a
        # second bind to the same address failing while the first instance holds it.
        sock.bind((HOST, PORT))
        sock.listen(8)
    except OSError:
        # Port busy. If a running iActivator answers the handshake, defer to it.
        if _ping_primary():
            return False
        return True  # unrelated listener on the port; start anyway, without the lock
    _sock = sock
    _serve(sock, on_show)
    return True


def release() -> None:
    global _sock
    if _sock is not None:
        try:
            _sock.close()
        finally:
            _sock = None
