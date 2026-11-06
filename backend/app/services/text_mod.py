from __future__ import annotations

import sys
from pathlib import Path

from ..config import BASE_DIR

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.text_rules import (  # noqa: E402
    LABEL_ZH, keyword_predict, keyword_predict_raw, normalize, perturb_variants,
)

MODEL_PATH = BASE_DIR / "ml" / "weights" / "text_model.joblib"
ROBUST_PATH = BASE_DIR / "ml" / "weights" / "text_model_robust.joblib"


class _State:
    clean = None
    robust = None
    loaded = False


def _load() -> None:
    if _State.loaded:
        return
    _State.loaded = True
    try:
        import joblib

        if MODEL_PATH.exists():
            _State.clean = joblib.load(MODEL_PATH)
        if ROBUST_PATH.exists():
            _State.robust = joblib.load(ROBUST_PATH)
    except Exception:
        _State.clean = None
        _State.robust = None


def available() -> bool:
    _load()
    return _State.clean is not None


def _from_rule(result: tuple[str, float], source: str) -> dict:
    label, score = result
    return {"label": label, "label_zh": LABEL_ZH.get(label, label), "score": round(score, 4), "source": source}


def _predict_with(model, text: str) -> dict:
    proba = model.predict_proba([text])[0]
    classes = list(model.classes_)
    idx = int(proba.argmax())
    label = classes[idx]
    return {
        "label": label,
        "label_zh": LABEL_ZH.get(label, label),
        "score": round(float(proba[idx]), 4),
        "probs": {c: round(float(p), 4) for c, p in zip(classes, proba)},
        "source": "model",
    }


def predict_raw(text: str) -> dict:
    """等级 0：关键词基线，不做归一化。"""
    return _from_rule(keyword_predict_raw(text), "keyword")


def predict(text: str) -> dict:
    """等级 1：归一化 + 关键词基线。"""
    return _from_rule(keyword_predict(text), "keyword-normalized")


def predict_robust(text: str) -> dict:
    """等级 2：归一化 + 对抗训练模型。"""
    _load()
    model = _State.robust or _State.clean
    if model is None:
        return _from_rule(keyword_predict(text), "keyword-normalized")
    return _predict_with(model, normalize(text))


def make_variants(text: str, n: int = 4) -> list[dict]:
    return perturb_variants(text, n)
