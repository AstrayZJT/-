from __future__ import annotations

import json
import threading

from ..config import DATA_DIR

_PATH = DATA_DIR / "settings.json"
_LOCK = threading.Lock()
_DEFAULT = {"defense_level": 0, "auto_moderate": True}

LEVELS = {
    0: "基线：关键词黑名单（1fps 抽帧）",
    1: "归一化：归一化 + 关键词（1fps 抽帧）",
    2: "增强：归一化 + 模型 + 0.4s 密采样",
}


def _read() -> dict:
    try:
        return {**_DEFAULT, **json.loads(_PATH.read_text(encoding="utf-8"))}
    except Exception:
        return dict(_DEFAULT)


def get_settings() -> dict:
    with _LOCK:
        return _read()


def update_settings(**kwargs) -> dict:
    with _LOCK:
        data = _read()
        data.update({k: v for k, v in kwargs.items() if v is not None})
        data["defense_level"] = int(data.get("defense_level", 0))
        _PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
