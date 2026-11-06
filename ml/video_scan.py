"""视频抽帧审核：按时间间隔采样，复用图像分类器。"""

from __future__ import annotations

from pathlib import Path

import cv2
from PIL import Image

from ml.image_model import predict


def scan_video(path: str | Path, rate: float = 1.0, model=None, threshold: float = 0.5,
               start: float = 0.0) -> dict:
    """按 rate（秒/帧）采样，start 用于模拟随机相位。"""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"samples": [], "violations": [], "error": "无法打开视频"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps if total else 0.0

    samples = []
    next_t = start
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = idx / fps
        if t + 1e-6 >= next_t:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            label, score = predict(img, model)
            samples.append({"t": round(t, 2), "label": label, "score": round(score, 4)})
            next_t += rate if rate > 0 else 1.0
        idx += 1
    cap.release()

    violations = []
    for s in samples:
        if s["label"] == "ad" and s["score"] >= threshold:
            violations.append({"start": s["t"], "end": round(s["t"] + rate, 2), "score": s["score"]})
    return {
        "duration": round(duration, 2),
        "fps": round(fps, 2),
        "rate": rate,
        "samples": samples,
        "violations": violations,
    }
