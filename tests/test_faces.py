import base64
import pathlib

import numpy as np
import pytest

from faces import THRESHOLD, Faces

PHOTO = pathlib.Path(__file__).parent / "data" / "astronaut.jpg"


def data_url(path_or_bytes):
    raw = (
        path_or_bytes
        if isinstance(path_or_bytes, bytes)
        else pathlib.Path(path_or_bytes).read_bytes()
    )
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


@pytest.fixture
def faces(tmp_path):
    return Faces(tmp_path / "t.db")


def test_status_explains_what_is_missing(faces):
    s = faces.status()
    assert isinstance(s["ready"], bool) and s["message"]


def test_names_and_delete(faces):
    faces.add("Alex")
    faces.add("Sam")
    assert faces.names() == ["Alex", "Sam"]
    faces.delete(faces.all()[0]["id"])
    assert faces.names() == ["Sam"]


def test_match_threshold_logic(faces):
    """Uses made-up embeddings, so it tests the decision rule, not the model."""
    import json

    e = np.zeros(128, dtype=np.float32)
    e[0] = 1
    faces.db.execute(
        "insert into faces(name,photo,emb) values('Alex','',?)", (json.dumps(e.tolist()),)
    )
    assert faces.match(e)[0] == "Alex"
    other = np.zeros(128, dtype=np.float32)
    other[1] = 1
    assert faces.match(other)[0] is None


needs_models = pytest.mark.skipif(
    not Faces(":memory:").status()["ready"], reason="run python models/download_models.py first"
)


@needs_models
def test_real_photo_is_recognised_after_resize_and_flip(faces, KoSa):
    import cv2

    assert faces.add("Eileen", data_url(PHOTO)) is True
    img = cv2.imread(str(PHOTO))
    small = cv2.flip(cv2.resize(img, None, fx=0.6, fy=0.6), 1)
    other_view = data_url(cv2.imencode(".jpg", small)[1].tobytes())
    emb, box, size = faces.analyse(other_view)
    name, score = faces.match(emb)
    assert name == "Eileen" and score >= THRESHOLD


@needs_models
def test_door_camera_announces_known_visitor(KoSa):
    KoSa.faces.add("Eileen", data_url(PHOTO))
    assert "Eileen" in KoSa.identify(data_url(PHOTO))
    assert KoSa.events[-1]["known"] is True and KoSa.events[-1]["box"]


@needs_models
def test_unknown_face_is_reported_as_stranger(KoSa):
    KoSa.faces.add("Someone Else")
    assert "don't recognise" in KoSa.identify(data_url(PHOTO))
    assert KoSa.events[-1]["known"] is False


@needs_models
def test_picture_without_a_face(KoSa):
    import cv2

    blank = data_url(cv2.imencode(".jpg", np.full((200, 200, 3), 128, np.uint8))[1].tobytes())
    assert "can't see a face" in KoSa.identify(blank)
    assert KoSa.events == []
