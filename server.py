import os
import re
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core import KoSa

HERE = Path(__file__).parent
app, KoSa = FastAPI(title="KoSa"), KoSa(os.environ.get("KoSa_HOME") or HERE / "home.json")


def out(reply=None):
    return {"reply": reply, **KoSa.snapshot()}


@app.get("/api/state")
def state():
    return out()


@app.post("/api/chat")
def chat(body: dict):
    return out(KoSa.chat(body.get("text", "")))


@app.post("/api/toggle")
def toggle(body: dict):
    return out(KoSa.toggle(body["id"]))


@app.post("/api/role")
def role(body: dict):
    KoSa.role = "guest" if body.get("role") == "guest" else "owner"
    return out(f"Role set to {KoSa.role}.")


@app.get("/api/books")
def books(q: str = ""):
    return KoSa.lib.search(q)


@app.post("/api/camera/visit")
def visit(body: dict):
    return out(KoSa.visit(body.get("who", "Stranger")))


@app.get("/api/words")
def words():
    return KoSa.words.all()


@app.post("/api/words")
def add_word(body: dict):
    KoSa.words.add(body.get("kind", ""), body.get("word", ""), body.get("meaning", ""))
    return KoSa.words.all()


@app.delete("/api/words/{wid}")
def del_word(wid: int):
    KoSa.words.delete(wid)
    return KoSa.words.all()


@app.get("/api/camera/status")
def cam_status():
    return KoSa.faces.status()


@app.post("/api/camera/identify")
def identify(body: dict):
    return out(KoSa.identify(body.get("photo", "")))


@app.get("/api/people")
def people():
    return KoSa.faces.all()


@app.post("/api/people")
def add_person(body: dict):
    KoSa.faces.add(body.get("name", ""), body.get("photo", ""))
    return KoSa.faces.all()


@app.delete("/api/people/{pid}")
def del_person(pid: int):
    KoSa.faces.delete(pid)
    return KoSa.faces.all()


@app.get("/api/hardware")
def hardware():
    return {
        "pyserial": KoSa.hw.available(),
        "ports": KoSa.hw.ports(),
        "bindings": KoSa.hw.bindings(),
    }


@app.post("/api/hardware/bind")
def hw_bind(body: dict):
    ch = str(body.get("channel", "")).upper()
    if body["device"] not in KoSa.devs or not re.fullmatch(r"D([2-9]|1[0-3])", ch):
        return {"ok": False, "message": "Pick a pin between D2 and D13, for example D13."}
    ok, err = KoSa.hw.ping(body.get("port", ""))
    if ok:
        KoSa.hw.bind(body["device"], body["port"], ch)
        KoSa.push(body["device"])
    return {"ok": ok, "message": "Paired. The board now follows this device." if ok else err}


@app.delete("/api/hardware/bind/{device}")
def hw_unbind(device: str):
    KoSa.hw.unbind(device)
    return {"ok": True}


@app.post("/api/hardware/test")
def hw_test(body: dict):
    k = body["device"]
    ok, err = KoSa.hw.send(k, "on")
    if ok:
        time.sleep(0.6)
        KoSa.push(k)
    return {
        "ok": ok,
        "message": (
            "The device switched on briefly, then went back to its normal state."
            if ok
            else f"Couldn't reach it: {err}"
        ),
    }


app.mount("/", StaticFiles(directory=HERE / "static", html=True))
