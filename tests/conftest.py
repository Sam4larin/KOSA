import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import KoSa  # noqa: E402


@pytest.fixture
def KoSa(tmp_path):
    """A KoSa instance with its own empty database."""
    shutil.copy(ROOT / "home.json", tmp_path / "home.json")
    return KoSa(tmp_path / "home.json")
