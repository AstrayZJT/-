from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.text_rules import (  # noqa: E402
    LABELS, keyword_predict, keyword_predict_raw, normalize, perturb_variants,
)

WEIGHTS = ROOT / "ml" / "weights"
WEIGHTS.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> tuple[list[str], list[str]]:
    texts, labels = [], []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            texts.append(row["text"])
            labels.append(row["label"])
    return texts, labels


def build() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=1,
                                  max_features=40000, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=4000, C=8.0, class_weight="balanced")),
    ])


def main() -> None:
    train_x, train_y = load_csv(ROOT / "data" / "seed" / "text_train.csv")
    test_x, test_y = load_csv(ROOT / "data" / "seed" / "text_test.csv")

    clean = build().fit(train_x, train_y)
    clean_pred = clean.predict(test_x)
    clean_acc = accuracy_score(test_y, clean_pred)

    # 对抗训练：原文 + 变体 + 归一化后的变体（正常/违规都加）
    aug_x, aug_y = list(train_x), list(train_y)
    for text, label in zip(train_x, train_y):
        for v in perturb_variants(text, n=2):
            aug_x.append(v["text"])
            aug_y.append(label)
            aug_x.append(normalize(v["text"]))
            aug_y.append(label)
    robust = build().fit(aug_x, aug_y)
    robust_pred = robust.predict(test_x)

    kw_acc = sum(keyword_predict_raw(t)[0] == y for t, y in zip(test_x, test_y)) / len(test_y)
    kwn_acc = sum(keyword_predict(t)[0] == y for t, y in zip(test_x, test_y)) / len(test_y)
    model_acc = sum(clean.predict([normalize(t)])[0] == y for t, y in zip(test_x, test_y)) / len(test_y)

    # 攻击评测：三种防线，四种变体
    results: dict[str, dict] = {}
    for vtype in ["同音/形近（全量）", "零宽字符", "字符拆分", "Emoji 插入"]:
        total = kw_evade = norm_evade = model_evade = 0
        for text, label in zip(test_x, test_y):
            if label == "normal":
                continue
            variant = next((v for v in perturb_variants(text, n=6) if v["type"] == vtype), None)
            if variant is None:
                continue
            total += 1
            raw = variant["text"]
            if keyword_predict_raw(raw)[0] == "normal":
                kw_evade += 1
            if keyword_predict(raw)[0] == "normal":
                norm_evade += 1
            if robust.predict([normalize(raw)])[0] == "normal":
                model_evade += 1
        if total:
            results[vtype] = {
                "samples": total,
                "keyword_evasion": round(kw_evade / total, 4),
                "normalize_evasion": round(norm_evade / total, 4),
                "model_evasion": round(model_evade / total, 4),
            }

    metrics = {
        "task": "text_moderation",
        "train_size": len(train_x),
        "test_size": len(test_x),
        "keyword_accuracy": round(kw_acc, 4),
        "keyword_normalized_accuracy": round(kwn_acc, 4),
        "model_accuracy": round(model_acc, 4),
        "clean_accuracy": round(clean_acc, 4),
        "clean_macro_f1": round(f1_score(test_y, clean_pred, average="macro"), 4),
        "robust_accuracy": round(accuracy_score(test_y, robust_pred), 4),
        "robust_macro_f1": round(f1_score(test_y, robust_pred, average="macro"), 4),
        "per_class": classification_report(test_y, clean_pred, output_dict=True, zero_division=0),
        "attack_evasion": results,
        "labels": LABELS,
        "note": "关键词基线模拟平台早期只有黑名单的状态；归一化防御成本最低；模型用于兜住归一化处理不了的变体。",
    }

    joblib.dump(clean, WEIGHTS / "text_model.joblib")
    joblib.dump(robust, WEIGHTS / "text_model_robust.joblib")
    (WEIGHTS / "text_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: metrics[k] for k in (
        "keyword_accuracy", "keyword_normalized_accuracy", "model_accuracy", "robust_accuracy")}, ensure_ascii=False))
    for k, v in results.items():
        print(k, v)


if __name__ == "__main__":
    main()
