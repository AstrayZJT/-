"""小型 CNN：广告图 vs 正常图。用于课堂演示，不追求 SOTA。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

try:  # torch 是可选依赖：没装时后端会退化为规则/启发式
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore
    nn = None  # type: ignore
    TORCH_AVAILABLE = False

IMG_SIZE = 96
CLASSES = ["normal", "ad"]
CLASS_ZH = {"normal": "正常", "ad": "广告导流"}


if TORCH_AVAILABLE:

    class SmallCNN(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            )
            self.head = nn.Sequential(
                nn.AdaptiveAvgPool2d(1), nn.Flatten(),
                nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 2),
            )

        def forward(self, x):  # noqa: ANN001
            return self.head(self.features(x))

    def load_model(path: str | Path):
        model = SmallCNN()
        state = torch.load(str(path), map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        return model

    def to_tensor(img: Image.Image):
        arr = np.asarray(img.convert("RGB").resize((IMG_SIZE, IMG_SIZE)), dtype=np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        return torch.from_numpy(arr).unsqueeze(0)

    def tensor_to_pil(x) -> Image.Image:
        arr = (x.detach().clamp(0, 1)[0].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
        return Image.fromarray(arr)

    def predict_probs(img: Image.Image, model) -> tuple[str, float, "torch.Tensor"]:
        x = to_tensor(img)
        with torch.no_grad():
            probs = torch.softmax(model(x), dim=1)[0]
        idx = int(probs.argmax())
        return CLASSES[idx], float(probs[idx]), probs

    def predict(img: Image.Image, model=None) -> tuple[str, float]:
        if model is None:
            model = load_model(Path(__file__).parent / "weights" / "image_model.pt")
        label, score, _ = predict_probs(img, model)
        return label, score

    def fgsm(model, x, target_idx: int = 0, eps: float = 8 / 255):
        """把图片往 target_idx（默认 normal）方向推。"""
        x_adv = x.clone().detach().requires_grad_(True)
        logits = model(x_adv)
        target = torch.full((x.size(0),), target_idx, dtype=torch.long)
        loss = nn.CrossEntropyLoss()(logits, target)
        grad = torch.autograd.grad(loss, x_adv)[0]
        adv = x_adv - eps * grad.sign()
        return torch.clamp(adv, 0, 1).detach()

    def pgd(model, x, target_idx: int = 0, eps: float = 8 / 255, steps: int = 10) -> "torch.Tensor":
        x_adv = x.clone().detach()
        target = torch.full((x.size(0),), target_idx, dtype=torch.long)
        alpha = eps / 4
        for _ in range(steps):
            x_adv.requires_grad_(True)
            logits = model(x_adv)
            loss = nn.CrossEntropyLoss()(logits, target)
            grad = torch.autograd.grad(loss, x_adv)[0]
            with torch.no_grad():
                x_adv = x_adv - alpha * grad.sign()
                x_adv = torch.clamp(x_adv, x - eps, x + eps)
                x_adv = torch.clamp(x_adv, 0, 1)
        return x_adv.detach()
