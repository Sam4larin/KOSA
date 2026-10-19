import importlib
import pathlib
import shutil

import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def client(tmp_path, monkeypatch):
    shutil.copy(ROOT / "home.json", tmp_path / "home.json")
    monkeypatch.setenv("KoSa_HOME", str(tmp_path / "home.json"))
    import server

    importlib.reload(server)
    return TestClient(server.app)


def test_page_is_served(client):
    assert "KoSa" in client.get("/").text


def test_chat_and_toggle(client):
    assert (
        "is on"
        in client.post("/api/chat", json={"text": "turn on the kitchen light"}).json()["reply"]
    )
    assert (
        client.post("/api/toggle", json={"id": "kitchen.light"}).json()["devices"]["kitchen.light"][
            "on"
        ]
        is False
    )


def test_people_crud(client):
    assert (
        client.post("/api/people", json={"name": "Alex", "photo": ""}).json()[0]["name"] == "Alex"
    )
    pid = client.get("/api/people").json()[0]["id"]
    assert client.delete(f"/api/people/{pid}").json() == []


def test_word_bank_crud(client):
    w = client.post(
        "/api/words", json={"kind": "action", "word": "illuminate", "meaning": "turn on"}
    ).json()
    assert w[0]["word"] == "illuminate"
    assert client.delete(f"/api/words/{w[0]['id']}").json() == []


def test_camera_status_and_identify_without_face(client):
    assert "ready" in client.get("/api/camera/status").json()
    assert client.post("/api/camera/identify", json={"photo": "nope"}).status_code == 200


def test_hardware_lists_the_simulator_ports(client):
    ports = [p["port"] for p in client.get("/api/hardware").json()["ports"]]
    assert "socket://localhost:5555" in ports


def test_bad_pin_is_refused(client):
    r = client.post(
        "/api/hardware/bind", json={"device": "kitchen.light", "port": "x", "channel": "X99"}
    ).json()
    assert r["ok"] is False
