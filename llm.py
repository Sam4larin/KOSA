"""Optional text generation through a local Ollama server."""

import json
import os
import urllib.request

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("KoSa_MODEL", "mistral:7b-instruct")
SYSTEM = (
    "You are KoSa, a friendly home assistant. Keep answers under 80 words unless asked for a story."
)


def ask(prompt):
    try:
        request = urllib.request.Request(
            URL,
            json.dumps(
                {"model": MODEL, "prompt": prompt, "system": SYSTEM, "stream": False}
            ).encode(),
            {"Content-Type": "application/json"},
        )
        return json.load(urllib.request.urlopen(request, timeout=90))["response"].strip()
    except Exception:
        return None
