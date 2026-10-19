"""Downloads the two free OpenCV Zoo face models into this folder.
Run:  python models/download_models.py"""

import sys
import urllib.request
from pathlib import Path

BASE = "https://github.com/opencv/opencv_zoo/raw/main/models/"
FILES = {
    "face_detection_yunet_2023mar.onnx": BASE
    + "face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": BASE
    + "face_recognition_sface/face_recognition_sface_2021dec.onnx",
}
here = Path(__file__).parent
for name, url in FILES.items():
    dest = here / name
    if dest.exists() and dest.stat().st_size > 100_000:
        print(name, "is already here.")
        continue
    print("Downloading", name, "...")
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print("  failed:", e)
    if (
        not dest.exists() or dest.stat().st_size < 100_000
    ):  # a tiny file is a Git LFS pointer, not the model
        dest.unlink(missing_ok=True)
        print(
            f"  Couldn't download {name}.\n  Open {url.replace('/raw/', '/blob/')} in your browser,\n  use the download button there, and save the file in this folder."
        )
        sys.exit(1)
print("Done. Restart KoSa.")
