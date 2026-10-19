"""Home model, command parsing, safety checks and replies."""

import json
import random
import re
from datetime import datetime
from pathlib import Path

import llm
from drivers import Hardware
from faces import Faces
from library import Library
from wordbank import WordBank

VERBS = [
    ("unlock", "unlock"),
    ("lock", "lock"),
    ("turn on", "on"),
    ("switch on", "on"),
    ("turn off", "off"),
    ("switch off", "off"),
]
SCENES = {
    "good night": (
        [("light", "off"), ("lock", "lock")],
        "Good night. I've turned off the lights and locked the doors.",
    ),
    "good morning": ([("light", "on")], "Good morning! I've turned on the lights."),
}
TYPES = {
    "light": "light",
    "lights": "light",
    "lamp": "light",
    "fan": "fan",
    "fans": "fan",
    "door": "lock",
    "doors": "lock",
    "lock": "lock",
}
PLURAL = {"light": "lights", "fan": "fans", "lock": "doors"}
STATE = {"on": "on", "off": "off", "lock": "locked", "unlock": "unlocked"}
CONFIRM_WORDS = ("yes", "y", "yeah", "yep", "confirm", "ok", "sure")
ABOUT = (
    "I'm KoSa, your home assistant. I manage your smart home devices and library."
)
FALLBACK = (
    "I'm not sure what that is or how to do that yet. You can also teach me your own words in the Word Bank."
)
EMERGENCY = ("intruder", "break in", "broke in", "burglar", "thief", "ole")
MISHEARINGS = {
    "dawn on": "turn on",
    "tone on": "turn on",
    "ton on": "turn on",
    "turn of ": "turn off ",
}


def join(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def cap(s):
    return s[0].upper() + s[1:]


def pick(*o):
    return random.choice(o)


class KoSa:
    def __init__(self, path):
        cfg = json.loads(Path(path).read_text())
        db = Path(path).with_name("KoSa.db")
        self.name, self.rooms, self.devs = cfg["name"], cfg["rooms"], {}
        for r in self.rooms:
            for d in r["devices"]:
                key = f'{r["id"]}.{d["id"]}'
                self.devs[key] = {
                    **d,
                    "id": key,
                    "room": r["id"],
                    "on": False,
                    "locked": d["type"] == "lock",
                }
        self.events, self.lib, self.words, self.faces = [], Library(db), WordBank(db), Faces(db)
        self.hw = Hardware(db)
        self.role, self.pending, self.last_room, self.log, self._quiet = (
            "owner",
            None,
            None,
            [],
            False,
        )

    def snapshot(self):
        return {
            "name": self.name,
            "rooms": self.rooms,
            "devices": self.devs,
            "role": self.role,
            "log": self.log[-8:],
            "people": self.faces.names(),
            "events": self.events[-5:],
            "event_count": len(self.events),
        }

    def label(self, k):
        d = self.devs[k]
        room = next(r["name"] for r in self.rooms if r["id"] == d["room"]).lower()
        n = d["name"].lower()
        return "the " + (n if d["type"] == "lock" or room[:3] in n else f"{room} {n}")

    def _sentence(self, verb, keys, already=False):
        typ = self.devs[keys[0]]["type"]
        names = (
            [self.label(k) for k in keys] if len(keys) <= 3 else [f"all {len(keys)} {PLURAL[typ]}"]
        )
        return f"{cap(join(names))} {'are' if len(keys) > 1 else 'is'} {'already ' if already else ''}{STATE[verb]}."

    def _is(self, k, verb):
        d = self.devs[k]
        return (
            d["locked"]
            if verb == "lock"
            else (not d["locked"]) if verb == "unlock" else d["on"] if verb == "on" else not d["on"]
        )

    def _apply(self, verb, keys):
        failed = []
        for k in keys:
            if not self.hw.send(k, verb)[
                0
            ]:  # the board did not confirm, so keep the previous state
                failed.append(k)
                continue
            d = self.devs[k]
            if d["type"] == "lock":
                d["locked"] = verb == "lock"
            else:
                d["on"] = verb == "on"
        self.last_room = self.devs[keys[-1]]["room"]
        return failed

    def _current(self, k):
        """The verb that describes a device's present state."""
        d = self.devs[k]
        if d["type"] == "lock":
            return "lock" if d["locked"] else "unlock"
        return "on" if d["on"] else "off"

    def push(self, k):
        """Send a device's current state to its paired board."""
        return self.hw.send(k, self._current(k))

    def _do(self, verb, keys, confirmed=False):
        if not keys:
            return "I couldn't find a device like that. Which one did you mean?"
        if self.role == "guest" and verb in ("lock", "unlock"):
            return "Sorry, guests can't lock or unlock doors."
        if all(self._is(k, verb) for k in keys):
            return self._sentence(verb, keys, True)
        if verb == "unlock" and not confirmed:
            self.pending = (verb, keys)
            return f"Do you want me to unlock {join([self.label(k) for k in keys])}? Say yes to confirm."
        failed = self._apply(verb, keys)
        if failed:
            msg = f"I couldn't reach {join([self.label(k) for k in failed])}. Check that it's plugged in and paired on the Devices page."
            okk = [k for k in keys if k not in failed]
            msg = (self._sentence(verb, okk) + " " if okk else "") + msg
            self.log.append(msg)
            return msg
        s = self._sentence(verb, keys)
        self.log.append(s)
        return ("" if self._quiet else pick("Sure. ", "Okay. ", "Done. ", "", "")) + s

    def _targets(self, t, typ):
        words = set(re.findall(r"\w+", t))
        named = [k for k, d in self.devs.items() if d["type"] == typ and d["name"].lower() in t]
        if named:
            return named
        rooms = [r["id"] for r in self.rooms if r["name"].lower() in t]
        if not rooms:
            if words & {"all", "every", "house", "everything"}:
                rooms = [r["id"] for r in self.rooms]
            elif self.last_room:
                rooms = [self.last_room]
            else:
                return None
        return [k for k, d in self.devs.items() if d["type"] == typ and d["room"] in rooms]

    def toggle(self, key):
        opposite = {"lock": "unlock", "unlock": "lock", "on": "off", "off": "on"}
        return self._do(opposite[self._current(key)], [key])

    def visit(self, who, photo="", box=None, size=None, score=None):
        """Record a visitor at the door."""
        known = who in self.faces.names()
        msg = (
            pick(f"{who} is at the front door.", f"Looks like {who} is at the front door.")
            if known
            else "Someone I don't recognise is at the front door."
        )
        self.events.append(
            {
                "who": who if known else "Unknown",
                "known": known,
                "msg": msg,
                "time": datetime.now().strftime("%H:%M:%S"),
                "photo": photo,
                "box": box,
                "size": size,
                "score": score,
            }
        )
        self.log.append(msg)
        return msg

    def identify(self, photo):
        """Match the face in a photo against the people KoSa knows."""
        st = self.faces.status()
        if not st["ready"]:
            return "Face recognition isn't set up yet. " + st["message"]
        a = self.faces.analyse(photo)
        if a is None:
            return "I can't see a face in that picture. Try a clearer photo that faces the camera."
        emb, box, size = a
        name, score = self.faces.match(emb)
        return self.visit(name or "Unknown", photo, box, size, score)

    def _ai(self, prompt, flag=False):
        out = llm.ask(prompt)
        if out is None:
            return (
                "I'd need Ollama running to do that. You can start it with 'ollama serve'."
                if flag
                else None
            )
        return ("(AI-generated, may contain errors) " if flag else "") + out

    def chat(self, text, _nested=False):
        """Turn one message from the user into a reply, acting on the home when asked."""
        t = text.lower().strip()
        if self.pending:
            return self._answer_confirmation(t)
        if not _nested:
            commands = self.words.phrase(t)
            if commands:
                return self._run_phrase(commands)
        t = self.words.rewrite(t)
        for wrong, right in MISHEARINGS.items():
            t = t.replace(wrong, right)
        words = set(re.findall(r"\w+", t))
        for handler in (
            self._emergency,
            self._scene,
            self._status,
            self._state_question,
            self._door_question,
            self._small_talk,
            self._book_request,
            self._device_command,
        ):
            reply = handler(t, words, text)
            if reply:
                return reply
        return self._ai(text) or FALLBACK

    def _answer_confirmation(self, t):
        verb, keys = self.pending
        self.pending = None
        if t in CONFIRM_WORDS:
            return self._do(verb, keys, True)
        return "Okay, I'll leave it as it is."

    def _run_phrase(self, commands):
        self._quiet = True
        try:
            return " ".join(self.chat(c, True) for c in commands)
        finally:
            self._quiet = False

    def _emergency(self, t, words, text):
        if not any(w in t for w in EMERGENCY):
            return None
        self._apply("lock", self._of_type("lock"))
        return (
            "I've locked every door. If you're in danger, "
            "please call your local emergency number right away."
        )

    def _scene(self, t, words, text):
        for name, (steps, reply) in SCENES.items():
            if name not in t:
                continue
            if self.role == "guest" and any(typ == "lock" for typ, _ in steps):
                return "Sorry, only the owner can do that."
            failed = []
            for typ, verb in steps:
                failed += self._apply(verb, self._of_type(typ))
            if failed:
                reply += f" I couldn't reach {join([self.label(k) for k in failed])}."
            self.log.append(reply)
            return reply
        return None

    def _status(self, t, words, text):
        if not ("status" in t or "what's on" in t or "whats on" in t):
            return None
        on = [self.label(k) for k, d in self.devs.items() if d["on"]]
        unlocked = [
            self.label(k) for k, d in self.devs.items() if d["type"] == "lock" and not d["locked"]
        ]
        first = (
            f"{cap(join(on))} {'are' if len(on) > 1 else 'is'} on." if on else "Everything is off."
        )
        second = (
            f"{cap(join(unlocked))} {'are' if len(unlocked) > 1 else 'is'} unlocked."
            if unlocked
            else "All the doors are locked."
        )
        return f"{first} {second}"

    def _state_question(self, t, words, text):
        if t.split()[:1] not in (["is"], ["are"]):
            return None
        typ = next((TYPES[w] for w in re.findall(r"\w+", t) if w in TYPES), None)
        keys = self._targets(t, typ) if typ else None
        if not keys:
            return None
        return " ".join(self._sentence(self._current(k), [k]) for k in keys[:4])

    def _door_question(self, t, words, text):
        if re.search(r"who(?:'s| is) (?:at )?the (?:front )?door|who(?:'s| is) there", t):
            event = self.events[-1] if self.events else None
            if not event:
                return "Nobody has come to the door so far."
            return f"{event['msg']} (at {event['time']})"
        return None

    def _small_talk(self, t, words, text):
        if re.search(r"\bwho are you\b|\byour name\b", t):
            return ABOUT
        if re.match(r"(hi|hello|hey)\b", t) and len(words) <= 3:
            return pick("Hi! What can I do for you?", "Hello! How can I help?")
        if re.match(r"thank", t):
            return pick("You're welcome!", "Any time.")
        return None

    def _book_request(self, t, words, text):
        reply = self.lib.handle(text.strip(), self.rooms)
        if reply:
            return reply
        match = re.match(
            r"(?:summari[sz]e|summary of|tell me about the book)\s+(?:the book\s+)?(.+)", t
        )
        if match:
            return self._ai(
                f'Summarize the book "{match.group(1)}" in about 5 sentences. '
                "If you do not know it, say so.",
                True,
            )
        if t.startswith("tell me a story"):
            return self._ai(text + ". Keep it under 200 words.", True)
        return None

    def _device_command(self, t, words, text):
        verb = next((v for p, v in VERBS if p in t), None)
        if verb is None and words & {"turn", "switch"}:
            verb = "on" if "on" in words else "off" if "off" in words else None
        if not verb:
            return None
        if verb in ("lock", "unlock"):
            typ = "lock"
        else:
            typ = next((TYPES[w] for w in re.findall(r"\w+", t) if w in TYPES), None)
        if not typ:
            return "Which one: the lights, the fans or the doors?"
        keys = self._targets(t, typ)
        return self._do(verb, keys) if keys is not None else "Which room do you mean?"

    def _of_type(self, typ):
        return [k for k, d in self.devs.items() if d["type"] == typ]
