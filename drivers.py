"""Serial driver. Unpaired devices stay simulated; paired ones talk to a USB board.

Protocol, one text line each way: PING -> PONG, and D<pin> ON|OFF|LOCK|UNLOCK -> OK.
"""

import sqlite3
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

CMD = {"on": "ON", "off": "OFF", "lock": "LOCK", "unlock": "UNLOCK"}


class Hardware:
    SETTLE = 2.0  # seconds to wait after opening a port, while the board resets

    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "create table if not exists bindings(device text primary key, port text, channel text)"
        )
        self.conns = {}

    def available(self):
        return serial is not None

    def ports(self):
        if not serial:
            return []
        real = [
            {"port": p.device, "desc": p.description} for p in serial.tools.list_ports.comports()
        ]
        return real + [
            {
                "port": "socket://localhost:5555",
                "desc": "KoSa test board (run hardware/fake_board.py)",
            },
            {"port": "rfc2217://localhost:4000", "desc": "Wokwi simulator (VS Code extension)"},
        ]

    def bindings(self):
        return {
            d: {"port": p, "channel": c}
            for d, p, c in self.db.execute("select device,port,channel from bindings")
        }

    def bind(self, device, port, channel):
        self.db.execute("insert or replace into bindings values(?,?,?)", (device, port, channel))
        self.db.commit()

    def unbind(self, device):
        self.db.execute("delete from bindings where device=?", (device,))
        self.db.commit()

    def _talk(self, port, line):
        if serial is None:
            raise RuntimeError("USB support isn't installed (pip install pyserial)")
        s = self.conns.get(port)
        if s is None or not s.is_open:
            s = serial.serial_for_url(port, baudrate=9600, timeout=2)
            time.sleep(self.SETTLE)
            self.conns[port] = s
        s.reset_input_buffer()
        s.write((line + "\n").encode())
        return s.readline().decode(errors="ignore").strip()

    def ping(self, port):
        try:
            ok = self._talk(port, "PING") == "PONG"
            return ok, "" if ok else "The board didn't answer. Is the KoSa sketch uploaded to it?"
        except Exception:
            self.conns.pop(port, None)
            return (
                False,
                f"I couldn't open {port or 'that port'}. Is the board plugged in, and is another program (like the Arduino Serial Monitor) using it?",
            )

    def send(self, key, verb):
        """Return (ok, error). Unpaired devices are simulated and always succeed."""
        b = self.bindings().get(key)
        if not b:
            return True, ""
        try:
            ok = self._talk(b["port"], f'{b["channel"]} {CMD[verb]}') == "OK"
            return ok, "" if ok else "no confirmation from the board"
        except Exception as e:
            self.conns.pop(b["port"], None)
            return False, str(e)
