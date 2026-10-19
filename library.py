"""Personal library."""

import re
import sqlite3


class Library:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "create table if not exists books(id integer primary key, title text, author text, room text, shelf text)"
        )

    def add(self, title, author="", room="", shelf=""):
        self.db.execute(
            "insert into books(title,author,room,shelf) values(?,?,?,?)",
            (title, author, room, shelf),
        )
        self.db.commit()

    def search(self, q=""):
        like = f"%{q}%"
        rows = self.db.execute(
            "select title,author,room,shelf from books where title like ? or author like ? order by title",
            (like, like),
        )
        return [dict(zip(("title", "author", "room", "shelf"), r)) for r in rows]

    @staticmethod
    def fmt(b):
        where = (
            f', kept in the {b["room"]}' + (f' on shelf {b["shelf"]}' if b["shelf"] else "")
            if b["room"]
            else ""
        )
        return f'"{b["title"]}"' + (f' by {b["author"]}' if b["author"] else "") + where

    def handle(self, t, rooms):
        """Return a reply, or None if this isn't a library command."""
        m = re.match(r"add (?:the )?book (.+)", t, re.I)
        if m:
            rest, room, shelf = m.group(1), "", ""
            for r in rooms:
                mm = re.search(
                    r"\s+(?:in|to|on)\s+(?:the\s+)?"
                    + re.escape(r["name"])
                    + r"(?:\s+shelf\s+(\w+))?\s*$",
                    rest,
                    re.I,
                )
                if mm:
                    room, shelf, rest = r["name"], mm.group(1) or "", rest[: mm.start()]
                    break
            parts = re.split(r"\s+by\s+", rest, maxsplit=1, flags=re.I)
            b = {
                "title": parts[0].strip(" \"'"),
                "author": parts[1].strip() if len(parts) > 1 else "",
                "room": room,
                "shelf": shelf,
            }
            self.add(**b)
            return (
                "Added "
                + self.fmt(b)
                + "."
                + (
                    ""
                    if room
                    else " If you tell me which room it lives in, I can help you find it later."
                )
            )
        if re.match(r"(?:list|show) (?:my )?books|my books|what books do i have", t, re.I):
            bs = self.search()
            return (
                "Your library: " + "; ".join(map(self.fmt, bs))
                if bs
                else "Your library is empty. Try: add book Dune by Frank Herbert in the Study shelf 2"
            )
        m = re.match(r"books by (.+)", t, re.I)
        if m:
            bs = self.search(m.group(1))
            return "; ".join(map(self.fmt, bs)) if bs else f"No books by {m.group(1)}."
        m = re.match(
            r"(?:where(?:'s| is)|find|do i have)\s+(?:my copy of |the book |book |a book |the )?(.+?)\??$",
            t,
            re.I,
        )
        if m:
            bs = self.search(m.group(1))
            if bs:
                return "Found it: " + "; ".join(map(self.fmt, bs)) + "."
            if re.search(r"book|copy|do i have", t, re.I):
                return f'No book matching "{m.group(1)}" in your library.'
        return None
