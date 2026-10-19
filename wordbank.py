"""The user's own vocabulary: action words, nicknames, multi-step phrases and mishearing fixes."""

import re
import sqlite3


class WordBank:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "create table if not exists words(id integer primary key, kind text, word text, meaning text)"
        )

    def add(self, kind, word, meaning):
        if kind in ("action", "name", "phrase", "heard") and word.strip() and meaning.strip():
            self.db.execute(
                "insert into words(kind,word,meaning) values(?,?,?)",
                (kind, word.strip().lower(), meaning.strip()),
            )
            self.db.commit()

    def delete(self, i):
        self.db.execute("delete from words where id=?", (i,))
        self.db.commit()

    def all(self):
        return [
            dict(zip(("id", "kind", "word", "meaning"), r))
            for r in self.db.execute("select id,kind,word,meaning from words order by kind,word")
        ]

    def phrase(self, t):
        for w in self.all():
            if w["kind"] == "phrase" and re.search(rf"\b{re.escape(w['word'])}\b", t):
                return [c.strip() for c in w["meaning"].split(";") if c.strip()]

    def rewrite(self, t):
        for w in sorted(self.all(), key=lambda w: -len(w["word"])):
            if w["kind"] in ("action", "name", "heard"):
                t = re.sub(rf"\b{re.escape(w['word'])}\b", w["meaning"].lower(), t)
        return t
