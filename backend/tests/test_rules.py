from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.text_rules import (  # noqa: E402
    keyword_predict, keyword_predict_raw, normalize, perturb_variants,
)


def test_normalize_homophone() -> None:
    assert "微信" in normalize("加薇信 abc123")
    assert "兼职" in normalize("兼 职")
    assert "日结" in normalize("曰结")


def test_normalize_zero_width() -> None:
    raw = "加\u200b微\u200c信"
    assert normalize(raw) == "加微信"


def test_normalize_latin_spacing() -> None:
    assert normalize("Q Q 123") == "qq123"


def test_keyword_baseline_evaded_but_normalized_caught() -> None:
    variant = next(v for v in perturb_variants("加微信 abc123 兼职日结") if "同音" in v["type"])
    assert keyword_predict_raw(variant["text"])[0] == "normal"
    assert keyword_predict(variant["text"])[0] == "ad"


def test_variants_cover_four_types() -> None:
    variants = perturb_variants("加微信 abc123 兼职日结")
    types = {v["type"] for v in variants}
    assert len(variants) == 4
    assert any("同音" in t for t in types)
    assert "零宽字符" in types
    assert "字符拆分" in types
    assert "Emoji 插入" in types
    assert all(v["text"] != "加微信 abc123 兼职日结" for v in variants)


def test_abuse_detection() -> None:
    assert keyword_predict("你就是个傻X")[0] == "abuse"
