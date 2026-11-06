from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

from ..config import BASE_DIR

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.image_model import (  # noqa: E402
    CLASS_ZH, TORCH_AVAILABLE, load_model, pgd, predict_probs, tensor_to_pil, to_tensor,
)

MODEL_PATH = BASE_DIR / "ml" / "weights" / "image_model.pt"
ADV_PATH = BASE_DIR / "ml" / "weights" / "image_model_adv.pt"

_state: dict = {"clean": None, "adv": None, "tried": False}


def _get(adv: bool = False):
    if not _state["tried"]:
        _state["tried"] = True
        if TORCH_AVAILABLE:
            try:
                if MODEL_PATH.exists():
                    _state["clean"] = load_model(MODEL_PATH)
                if ADV_PATH.exists():
                    _state["adv"] = load_model(ADV_PATH)
            except Exception:
                _state["clean"] = None
    return _state["adv"] if adv and _state["adv"] is not None else _state["clean"]


def available() -> bool:
    return TORCH_AVAILABLE and _get() is not None


def _heuristic(img: Image.Image) -> tuple[str, float]:
    """无模型兜底：高饱和 + 大面积暖色，判为广告图。"""
    arr = np.asarray(img.convert("RGB").resize((96, 96)), dtype=np.float32) / 255.0
    mx, mn = arr.max(axis=2), arr.min(axis=2)
    sat = float((mx - mn).mean())
    warm = float(((arr[:, :, 0] > 0.6) & (arr[:, :, 1] > 0.45) & (arr[:, :, 2] < 0.5)).mean())
    score = min(0.95, 0.4 + sat * 0.6 + warm * 0.8)
    if sat > 0.25 and warm > 0.15:
        return "ad", round(score, 4)
    return "normal", round(1 - score * 0.5, 4)


def predict_image(path: str | Path, adv: bool = False) -> dict:
    img = Image.open(path)
    model = _get(adv)
    if model is None:
        label, score = _heuristic(img)
        return {"label": label, "label_zh": CLASS_ZH.get(label, label), "score": score, "source": "rule"}
    label, score, probs = predict_probs(img, model)
    return {
        "label": label,
        "label_zh": CLASS_ZH.get(label, label),
        "score": round(score, 4),
        "probs": {"normal": round(float(probs[0]), 4), "ad": round(float(probs[1]), 4)},
        "source": "model",
    }


def run_attack(path: str | Path, eps: float = 24 / 255, use_adv_model: bool = False) -> dict:
    """对一张图做 PGD（20 步），目标是让分类器判成 normal。"""
    model = _get(use_adv_model)
    img = Image.open(path)
    if model is None:
        return {"error": "图像模型不可用", "before": predict_image(path), "after": None}
    x = to_tensor(img)
    before = predict_probs(img, model)
    x_adv = pgd(model, x, target_idx=0, eps=eps, steps=20)
    adv_img = tensor_to_pil(x_adv)
    after = predict_probs(adv_img, model)
    return {
        "before": {"label": before[0], "score": round(before[1], 4)},
        "after": {"label": after[0], "score": round(after[1], 4)},
        "eps": eps,
        "method": "PGD-20",
        "adv_image": adv_img,
    }
