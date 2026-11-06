"""训练图像审核 CNN，并做 FGSM 攻击与对抗训练防御。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.image_model import (  # noqa: E402
    CLASSES, IMG_SIZE, SmallCNN, TORCH_AVAILABLE, fgsm, pgd, to_tensor,
)

if TORCH_AVAILABLE:
    import torch
    import torch.nn as nn

WEIGHTS = ROOT / "ml" / "weights"
WEIGHTS.mkdir(parents=True, exist_ok=True)
SEED_IMAGES = ROOT / "data" / "seed" / "images"


def load_split(split: str) -> tuple[list[Path], list[int]]:
    paths, labels = [], []
    for idx, name in enumerate(CLASSES):
        folder = SEED_IMAGES / split / name
        for p in sorted(folder.glob("*.jpg")):
            paths.append(p)
            labels.append(idx)
    return paths, labels


def batch_tensor(paths: list[Path]):
    xs = [to_tensor(Image.open(p))[0] for p in paths]
    return torch.stack(xs)


def evaluate(model, paths: list[Path], labels: list[int]) -> float:
    model.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, len(paths), 32):
            x = batch_tensor(paths[i:i + 32])
            y = torch.tensor(labels[i:i + 32])
            pred = model(x).argmax(dim=1)
            correct += int((pred == y).sum())
    return correct / len(paths)


def train(epochs: int, adv: bool = False, eps: float = 8 / 255, base: SmallCNN | None = None):
    paths, labels = load_split("train")
    model = base or SmallCNN()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    n = len(paths)
    for epoch in range(epochs):
        model.train()
        order = np.random.permutation(n)
        total_loss = 0.0
        for i in range(0, n, 32):
            idx = order[i:i + 32]
            x = batch_tensor([paths[j] for j in idx])
            y = torch.tensor([labels[j] for j in idx])
            if adv:
                model.eval()
                x_adv = pgd(model, x, target_idx=0, eps=16 / 255, steps=3)
                model.train()
                x = torch.cat([x, x_adv])
                y = torch.cat([y, y])
            opt.zero_grad()
            out = model(x)
            loss = loss_fn(out, y)
            loss.backward()
            opt.step()
            total_loss += float(loss) * len(idx)
        print(f"epoch {epoch + 1}/{epochs} loss={total_loss / n:.4f}")
    return model


def attack_success(model, paths: list[Path], labels: list[int], eps: float = 24 / 255) -> float:
    """广告图被推成 normal 的比例（PGD，20 步）。"""
    model.eval()
    total = success = 0
    for p, y in zip(paths, labels):
        if y != CLASSES.index("ad"):
            continue
        x = to_tensor(Image.open(p))
        x_adv = pgd(model, x, target_idx=0, eps=eps, steps=20)
        with torch.no_grad():
            pred = int(model(x_adv).argmax(dim=1))
        total += 1
        success += int(pred == 0)
    return success / max(total, 1)


def main() -> None:
    if not TORCH_AVAILABLE:
        print("torch 不可用，跳过图像训练")
        return
    torch.manual_seed(7)
    np.random.seed(7)

    test_paths, test_labels = load_split("test")

    clean = train(epochs=8)
    clean_acc = evaluate(clean, test_paths, test_labels)
    asr_clean = attack_success(clean, test_paths, test_labels)
    torch.save(clean.state_dict(), WEIGHTS / "image_model.pt")

    robust = train(epochs=6, adv=True, base=clean)
    robust_acc = evaluate(robust, test_paths, test_labels)
    asr_robust = attack_success(robust, test_paths, test_labels)
    torch.save(robust.state_dict(), WEIGHTS / "image_model_adv.pt")

    metrics = {
        "task": "image_moderation",
        "train_size": len(load_split("train")[0]),
        "test_size": len(test_paths),
        "clean_accuracy": round(clean_acc, 4),
        "attack_success_rate": round(asr_clean, 4),
        "robust_accuracy": round(robust_acc, 4),
        "robust_attack_success_rate": round(asr_robust, 4),
        "epsilon": 24 / 255,
        "classes": CLASSES,
    }
    (WEIGHTS / "image_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    # 导出一张“确定能被绕过”的广告图，供演示时一键加载
    demo_dir = ROOT / "data" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    for p, y in zip(test_paths, test_labels):
        if y != CLASSES.index("ad"):
            continue
        x = to_tensor(Image.open(p))
        adv = pgd(clean, x, target_idx=0, eps=24 / 255, steps=20)
        with torch.no_grad():
            if int(clean(adv).argmax(dim=1)) == 0:
                (demo_dir / "sample_ad.jpg").write_bytes(p.read_bytes())
                break
    normal_paths = [p for p, y in zip(test_paths, test_labels) if y == 0]
    if normal_paths:
        (demo_dir / "sample_normal.jpg").write_bytes(normal_paths[0].read_bytes())

    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
