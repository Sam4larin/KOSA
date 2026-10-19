"""A pretend Arduino for testing KoSa with no hardware.
Run:  python hardware/fake_board.py
Then open KoSa's Devices page, choose "KoSa test board" as the port, and press Pair.
It speaks the same protocol as KoSa_device.ino and shows each pin changing in this window."""

import socket

pins = {}


def show():
    row = "   ".join(
        f"D{p}: {'ON  (high)' if v else 'off (low) '}" for p, v in sorted(pins.items())
    )
    print("   pins ->", row or "none used yet", flush=True)


def handle(line):
    parts = line.strip().upper().split(" ")
    if parts == ["PING"]:
        return "PONG"
    if (
        len(parts) == 2
        and parts[0][:1] == "D"
        and parts[0][1:].isdigit()
        and 2 <= int(parts[0][1:]) <= 13
        and parts[1] in ("ON", "OFF", "LOCK", "UNLOCK")
    ):
        pins[int(parts[0][1:])] = parts[1] in ("ON", "LOCK")
        show()
        return "OK"
    return "ERR"


srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", 5555))
srv.listen(1)
print("Fake board ready on 127.0.0.1:5555. Press Ctrl+C to stop.", flush=True)
while True:
    conn, _ = srv.accept()
    print("KoSa connected.", flush=True)
    buf = b""
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode(errors="ignore").strip()
                reply = handle(text)
                print(f"received {text!r}  ->  replied {reply}", flush=True)
                conn.sendall((reply + "\r\n").encode())
    print("KoSa disconnected.", flush=True)
