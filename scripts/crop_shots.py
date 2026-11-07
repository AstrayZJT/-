"""裁掉截图底部的空白，生成 briefing 用的紧凑版截图。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
BG = np.array([244, 245, 248])

TARGETS = [
    "view-01-feed.png",
    "view-04-moderation.png",
    "view-05-bots.png",
    "06a-lab-text-result.png",
    "06b-lab-image-result.png",
    "06c-lab-video-result.png",
    "03-dashboard-admin.png",
    "07-settings.png",
]

for name in TARGETS:
    path = SHOTS / name
    if not path.exists():
        continue
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img).astype(np.int16)
    diff = np.abs(arr - BG).sum(axis=2) > 30
    rows = np.where(diff.any(axis=1))[0]
    if len(rows) == 0:
        continue
    bottom = min(img.height, int(rows.max()) + 36)
    img.crop((0, 0, img.width, bottom)).save(SHOTS / f"crop-{name}")
    print(name, "->", bottom)
