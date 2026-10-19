"""Runs KoSa's real serial code against a pretend board that follows the same protocol as KoSa_device.ino."""

import socket
import threading

import pytest

import drivers

PORT = None


@pytest.fixture
def board():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    seen, state = [], {"connections": 0}

    def serve():
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            state["connections"] += 1
            buf = b""
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        text = line.decode().strip()
                        seen.append(text)
                        ok = text == "PING" or (
                            text.split(" ")[0] == "D13"
                            and text.split(" ")[1] in ("ON", "OFF", "LOCK", "UNLOCK")
                        )
                        conn.sendall(
                            (("PONG" if text == "PING" else "OK") if ok else "ERR").encode()
                            + b"\r\n"
                        )

    threading.Thread(target=serve, daemon=True).start()
    drivers.Hardware.SETTLE = 0
    yield f"socket://127.0.0.1:{srv.getsockname()[1]}", seen, state
    srv.close()


def test_ping(KoSa, board):
    assert KoSa.hw.ping(board[0]) == (True, "")


def test_paired_device_drives_the_board(KoSa, board):
    port, seen, _ = board
    KoSa.hw.bind("bedroom.bedside", port, "D13")
    assert "is on" in KoSa.chat("turn on the bedside light")
    KoSa.chat("turn off the bedside light")
    assert seen[-2:] == ["D13 ON", "D13 OFF"]


def test_one_connection_is_reused(KoSa, board):
    port, _, state = board
    KoSa.hw.bind("bedroom.bedside", port, "D13")
    for _ in range(3):
        KoSa.chat("turn on the bedside light")
        KoSa.chat("turn off the bedside light")
    assert state["connections"] == 1


def test_unreachable_board_keeps_old_state_and_says_so(KoSa):
    KoSa.hw.bind("kitchen.light", "socket://127.0.0.1:1", "D13")
    reply = KoSa.chat("turn on the kitchen light")
    assert "couldn't reach" in reply
    assert KoSa.devs["kitchen.light"]["on"] is False


def test_unpaired_devices_stay_simulated(KoSa, board):
    KoSa.hw.bind("bedroom.bedside", board[0], "D13")
    assert "is on" in KoSa.chat("turn on the kitchen light")
    assert "D13 ON" not in board[1]
