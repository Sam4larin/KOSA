"""People KoSa knows, with local face recognition (OpenCV YuNet detector and SFace recognizer)."""

import base64
import json
import sqlite3
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

MODELS = Path(__file__).parent / "models"
DETECTOR = MODELS / "face_detection_yunet_2023mar.onnx"
RECOGNIZER = MODELS / "face_recognition_sface_2021dec.onnx"
THRESHOLD = 0.363  # cosine similarity; the value OpenCV recommends for SFace


class Faces:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "create table if not exists faces(id integer primary key, name text unique, photo text)"
        )
        try:
            self.db.execute("alter table faces add column emb text")
        except sqlite3.OperationalError:
            pass
        self._det = self._rec = None

    def status(self):
        if cv2 is None:
            return {
                "ready": False,
                "message": "Face recognition needs OpenCV. Run: pip install opencv-python-headless numpy",
            }
        if not (DETECTOR.exists() and RECOGNIZER.exists()):
            return {
                "ready": False,
                "message": "Face models are missing. Run: python models/download_models.py",
            }
        return {
            "ready": True,
            "message": "Face recognition is on. Everything runs on this computer.",
        }

    def _load(self):
        if self._det is None:
            self._det = cv2.FaceDetectorYN.create(str(DETECTOR), "", (320, 320), 0.8)
            self._rec = cv2.FaceRecognizerSF.create(str(RECOGNIZER), "")

    def analyse(self, photo):
        """Return (embedding, box, image size) for the largest face in a data-URL photo, or None."""
        if not self.status()["ready"] or not photo.startswith("data:image/"):
            return None
        self._load()
        img = cv2.imdecode(
            np.frombuffer(base64.b64decode(photo.split(",", 1)[1]), np.uint8), cv2.IMREAD_COLOR
        )
        if img is None:
            return None
        h, w = img.shape[:2]
        if max(h, w) > 1600:
            k = 1600 / max(h, w)
            img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
            h, w = img.shape[:2]
        self._det.setInputSize((w, h))
        _, faces = self._det.detect(img)
        if faces is None or not len(faces):
            return None
        f = max(faces, key=lambda r: r[2] * r[3])
        e = self._rec.feature(self._rec.alignCrop(img, f))[0]
        return e / np.linalg.norm(e), [int(v) for v in f[:4]], (w, h)

    def add(self, name, photo=""):
        """Save a person. Return True if a face was found in the photo."""
        if not name.strip():
            return False
        photo = photo if photo.startswith("data:image/") and len(photo) < 3_000_000 else ""
        a = self.analyse(photo) if photo else None
        self.db.execute(
            "insert or replace into faces(name,photo,emb) values(?,?,?)",
            (name.strip(), photo, json.dumps([float(v) for v in a[0]]) if a else None),
        )
        self.db.commit()
        return a is not None

    def match(self, emb):
        """Return (name or None, best similarity)."""
        best, score = None, -1.0
        for name, e in self.db.execute("select name,emb from faces where emb is not null"):
            s = float(np.dot(emb, np.array(json.loads(e), dtype=np.float32)))
            if s > score:
                best, score = name, s
        return (best, score) if score >= THRESHOLD else (None, score)

    def delete(self, i):
        self.db.execute("delete from faces where id=?", (i,))
        self.db.commit()

    def all(self):
        return [
            {"id": i, "name": n, "photo": p, "ready": e is not None}
            for i, n, p, e in self.db.execute("select id,name,photo,emb from faces order by name")
        ]

    def names(self):
        return [r[0] for r in self.db.execute("select name from faces order by name")]
