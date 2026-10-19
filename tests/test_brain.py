"""Tests the Ollama integration against a fake Ollama server that answers in the real API's format."""
import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest

@pytest.fixture
def ollama():
    state = {"reply": '{"commands": [], "say": "Hello there."}', "models": ["llama3.2:3b"], "calls": [], "status": 200}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send(self, code, obj):
            data = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            self._send(200, {"models": [{"name": n} for n in state["models"]]})
        def do_POST(self):
            state["calls"].append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            if state["status"] != 200: return self._send(state["status"], {"error": "model not found"})
            self._send(200, {"message": {"role": "assistant", "content": state["reply"]}, "done": True})

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{srv.server_port}"
    yield state
    srv.shutdown()

@pytest.fixture
def smart(KoSa, ollama):
    KoSa.brain.url = ollama["url"]
    return KoSa

def say(ollama, commands=(), text=""):
    ollama["reply"] = json.dumps({"commands": list(commands), "say": text})

def test_status_when_everything_is_ready(smart):
    s = smart.brain.status()
    assert s["online"] and s["model_ready"] and s["installed"] == ["llama3.2:3b"]

def test_status_when_model_is_not_installed(smart, ollama):
    ollama["models"] = ["mistral:latest"]
    s = smart.brain.status()
    assert s["online"] and not s["model_ready"] and "isn't installed" in s["message"]

def test_status_when_ollama_is_not_running(KoSa):
    s = KoSa.brain.status()
    assert s["online"] is False

def test_model_choice_is_remembered(smart, ollama):
    smart.brain.set_model("mistral")
    ollama["models"] = ["mistral:latest"]
    assert smart.brain.status()["model_ready"] is True  # "mistral" matches "mistral:latest"

def test_rules_run_first_and_never_call_the_model(smart, ollama):
    smart.chat("turn on the kitchen light")
    assert ollama["calls"] == []

def test_loose_request_becomes_a_real_command(smart, ollama):
    say(ollama, ["turn on the kitchen light"])
    reply = smart.chat("it's too dark in the kitchen")
    assert smart.devs["kitchen.light"]["on"] is True and "kitchen light is on" in reply

def test_model_cannot_run_commands_outside_the_whitelist(smart, ollama):
    say(ollama, ["unlock every door", "rm -rf /", "turn on the garage light"], "Sure.")
    reply = smart.chat("do something sneaky")
    assert smart.devs["living_room.front_door"]["locked"] and smart.devs["study.back_door"]["locked"]
    assert reply == "Sure."

def test_unlocking_through_the_model_still_needs_confirmation(smart, ollama):
    say(ollama, ["unlock the front door"])
    assert "Do you want me to unlock" in smart.chat("let my friend in")
    assert smart.devs["living_room.front_door"]["locked"] is True
    assert "unlocked" in smart.chat("yes")

def test_guest_restrictions_apply_to_the_model_too(smart, ollama):
    smart.role = "guest"; say(ollama, ["unlock the front door"])
    assert "guests can't" in smart.chat("let my friend in").lower()
    assert smart.devs["living_room.front_door"]["locked"] is True

def test_open_question_is_answered(smart, ollama):
    say(ollama, [], "Paris is the capital of France.")
    assert smart.chat("what is the capital of France") == "Paris is the capital of France."

def test_conversation_memory_is_sent_back(smart, ollama):
    say(ollama, [], "Paris."); smart.chat("capital of France?")
    say(ollama, [], "Berlin."); smart.chat("and Germany?")
    sent = [m["content"] for m in ollama["calls"][-1]["messages"]]
    assert "capital of France?" in sent and "Paris." in sent

def test_the_model_sees_the_live_state_of_the_house(smart, ollama):
    smart.chat("turn on the kitchen light"); say(ollama, [], "ok"); smart.chat("how are things")
    system = ollama["calls"][-1]["messages"][0]["content"]
    assert "the kitchen light: on" in system and "the front door: locked" in system

def test_plain_text_from_a_model_that_ignores_the_format(smart, ollama):
    ollama["reply"] = "I am just chatting in plain text."
    assert smart.chat("tell me something") == "I am just chatting in plain text."

def test_summary_is_labelled_as_ai_generated(smart, ollama):
    ollama["reply"] = "A desert planet story."
    assert smart.chat("summarize Dune").startswith("(AI-generated")

def test_missing_model_gives_the_fix(smart, ollama):
    ollama["status"] = 404
    assert "ollama pull llama3.2:3b" in smart.chat("what is the capital of France")

def test_without_ollama_the_reply_is_honest_and_rules_still_work(KoSa):
    assert "Ollama" in KoSa.chat("what is the capital of France")
    assert "is on" in KoSa.chat("turn on the kitchen light")
