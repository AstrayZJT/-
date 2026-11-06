"""从测试集中挑选一张“确定能被 PGD 绕过”的广告图，供演示一键加载。"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.image_model import CLASSES, load_model, pgd, to_tensor  # noqa: E402

clean = load_model(ROOT / "ml" / "weights" / "image_model.pt")
test_dir = ROOT / "data" / "seed" / "images" / "test"
out = ROOT / "data" / "demo"
out.mkdir(parents=True, exist_ok=True)

for p in sorted((test_dir / "ad").glob("*.jpg")):
    x = to_tensor(Image.open(p))
    adv = pgd(clean, x, target_idx=0, eps=24 / 255, steps=20)
    with torch.no_grad():
        if int(clean(adv).argmax(dim=1)) == 0:
            (out / "sample_ad.jpg").write_bytes(p.read_bytes())
            print("sample_ad:", p.name)
            break

normal = sorted((test_dir / "normal").glob("*.jpg"))
if normal:
    (out / "sample_normal.jpg").write_bytes(normal[0].read_bytes())
    print("sample_normal:", normal[0].name)
