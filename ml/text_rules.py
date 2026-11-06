"""文本审核的规则层：归一化、对抗变体生成、关键词基线。

设计说明：
- 关键词基线代表“平台早期只有黑名单”的状态；
- 归一化把同音字、零宽字符、分隔符还原，是成本最低的防御；
- 机器学习模型则用来兜住 Emoji 插入、改写等归一化处理不了的变体。

归一化映射与攻击映射共用同一张表，保证攻防对比在同一语义空间内进行。
"""

from __future__ import annotations

import random
import re
import unicodedata

LABELS = ["normal", "ad", "abuse"]
LABEL_ZH = {"normal": "正常", "ad": "广告导流", "abuse": "辱骂攻击"}

ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff"

# 变体 -> 规范写法（防御侧归一化使用）
HOMOPHONE_MAP = {
    "薇信": "微信", "威信": "微信", "维信": "微信", "微芯": "微信",
    "v信": "微信", "vx": "微信", "wx": "微信", "weixin": "微信",
    "伽": "加", "珈": "加", "茄": "加",
    "曰结": "日结", "曰入": "日入", "兼只": "兼职",
    "刷単": "刷单", "反利": "返利",
    "傻x": "傻x", "儍": "傻", "煞笔": "傻逼", "沙比": "傻逼",
    "滾": "滚", "拉圾": "垃圾", "惡心": "恶心",
    "优 惠 券": "优惠券", "高 薪": "高薪",
}

# 规范写法 -> 攻击变体（攻击侧全量替换使用）
ATTACK_MAP = [
    ("微信", "薇信"), ("加", "伽"), ("兼职", "兼 职"), ("日结", "曰结"),
    ("日入", "曰入"), ("刷单", "刷 单"), ("返利", "反利"), ("代写", "代 写"),
    ("代刷", "代 刷"), ("扫码", "扫 码"), ("代理", "代 理"), ("私聊", "私 聊"),
    ("高薪", "高 薪"), ("优惠券", "优 惠 券"), ("QQ", "Q Q"), ("qq", "q q"),
    ("傻", "儍"), ("滚", "滾"), ("垃圾", "拉圾"), ("恶心", "惡心"),
    ("去死", "去 死"), ("废物", "废 物"), ("蠢", "惷"),
]

AD_KEYWORDS = [
    "微信", "加v", "加qq", "qq", "兼职", "日结", "刷单", "返利", "代写",
    "代刷", "扫码", "进群", "代理", "优惠券", "高薪", "日入", "私聊", "手续费",
]
ABUSE_KEYWORDS = [
    "傻", "滚", "垃圾", "恶心", "去死", "废物", "蠢", "闭嘴", "有病", "丢人",
]


def normalize(text: str) -> str:
    """防御侧归一化：全半角、零宽字符、同音字、分隔符。"""
    s = unicodedata.normalize("NFKC", text)
    s = re.sub(f"[{ZERO_WIDTH}]", "", s)
    s = s.lower()
    for k in sorted(HOMOPHONE_MAP, key=len, reverse=True):
        s = s.replace(k, HOMOPHONE_MAP[k])
    # 汉字之间的分隔符
    s = re.sub(r"(?<=[\u4e00-\u9fff])[\s·•.\-_*~|/]+(?=[\u4e00-\u9fff])", "", s)
    # 拉丁字母/数字之间的空格，处理 Q Q、1 2 3
    s = re.sub(r"(?<=[a-z0-9])[ ]+(?=[a-z0-9])", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def _hits(text: str) -> tuple[int, int]:
    ad = sum(1 for k in AD_KEYWORDS if k in text)
    abuse = sum(1 for k in ABUSE_KEYWORDS if k in text)
    return ad, abuse


def _verdict(ad: int, abuse: int) -> tuple[str, float]:
    if abuse >= 1 and abuse >= ad:
        return "abuse", min(0.55 + 0.12 * abuse, 0.99)
    if ad >= 1:
        return "ad", min(0.55 + 0.1 * ad, 0.99)
    return "normal", 0.9


def keyword_predict_raw(text: str) -> tuple[str, float]:
    """不做归一化的关键词基线。"""
    return _verdict(*_hits(text))


def keyword_predict(text: str) -> tuple[str, float]:
    """归一化之后的关键词基线。"""
    return _verdict(*_hits(normalize(text)))


def _full_homophone(text: str) -> str:
    out = text
    for old, new in ATTACK_MAP:
        out = out.replace(old, new)
    return out


def _insert_zero_width(text: str, ratio: float = 0.6) -> str:
    out = []
    for ch in text:
        out.append(ch)
        if ch.strip() and random.random() < ratio:
            out.append(random.choice(ZERO_WIDTH))
    return "".join(out)


def _split_chars(text: str, sep: str = "·") -> str:
    return sep.join(list(text))


def _emoji(text: str) -> str:
    """先做同音替换，再在字符间插入 Emoji：
    关键词与归一化都无法还原，只有模型能靠上下文识别。"""
    emojis = ["😊", "🔥", "✨", "👉", "🎉"]
    base = _full_homophone(text)
    out = []
    for ch in base:
        out.append(ch)
        if ch.strip():
            out.append(random.choice(emojis))
    return "".join(out)


def perturb_variants(text: str, n: int = 4) -> list[dict]:
    """生成黑盒对抗变体（语义不变，只改字符形态）。"""
    variants = [
        {"type": "同音/形近（全量）", "text": _full_homophone(text)},
        {"type": "零宽字符", "text": _insert_zero_width(text)},
        {"type": "字符拆分", "text": _split_chars(text)},
        {"type": "Emoji 插入", "text": _emoji(text)},
    ]
    seen, out = set(), []
    for v in variants:
        if v["text"] not in seen and v["text"] != text:
            seen.add(v["text"])
            out.append(v)
    return out[:n]
