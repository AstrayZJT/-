from __future__ import annotations

import sys
from pathlib import Path

from ..config import BASE_DIR

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.video_scan import scan_video  # noqa: E402

from . import image_mod  # noqa: E402


def analyze(path: str | Path, rate: float = 1.0, start: float = 0.0) -> dict:
    model = image_mod._get()
    if model is None:
        return {"error": "图像模型不可用", "samples": [], "violations": [], "rate": rate}
    return scan_video(path, rate=rate, model=model, start=start)
