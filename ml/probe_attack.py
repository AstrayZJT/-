from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.image_model import CLASSES, fgsm, load_model, pgd, predict_probs, to_tensor  # noqa: E402

model = load_model(ROOT / "ml" / "weights" / "image_model.pt")
paths = sorted((ROOT / "data" / "seed" / "images" / "test" / "ad").glob("*.jpg"))[:60]

for name, fn, eps in [
    ("fgsm8", fgsm, 8 / 255),
    ("fgsm16", fgsm, 16 / 255),
    ("fgsm24", fgsm, 24 / 255),
    ("pgd16", pgd, 16 / 255),
]:
    ok = 0
    for p in paths:
        x = to_tensor(Image.open(p))
        adv = fn(model, x, target_idx=0, eps=eps)
        label, score, _ = predict_probs(Image.fromarray(
            (adv.clamp(0, 1)[0].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
        ), model)
        ok += int(label == "normal")
    print(name, ok / len(paths))
