"""评测视频抽帧策略：固定 1fps 会漏掉采样间隙里的违规画面。"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.image_model import TORCH_AVAILABLE, load_model  # noqa: E402
from ml.video_scan import scan_video  # noqa: E402

WEIGHTS = ROOT / "ml" / "weights"
DEMO = ROOT / "data" / "demo"


def main() -> None:
    if not TORCH_AVAILABLE:
        print("torch 不可用，跳过视频评测")
        return
    model = load_model(WEIGHTS / "image_model.pt")

    def detect(path, rate=1.0):
        return len(scan_video(path, rate=rate, model=model)["violations"]) > 0

    fixed_gap = detect(DEMO / "ad_gap.mp4", 1.0)
    fixed_hit = detect(DEMO / "ad_hit.mp4", 1.0)
    fixed_normal = detect(DEMO / "normal.mp4", 1.0)

    # 0.4s 密采样 + 随机相位，多次试验估计命中率（违规画面只有 0.3s）
    random.seed(1)
    trials = 40
    hits = 0
    for _ in range(trials):
        offset = random.uniform(0, 0.4)
        samples = scan_video(DEMO / "ad_gap.mp4", rate=0.4, model=model, start=offset)["samples"]
        hits += int(any(s["label"] == "ad" for s in samples))
    random_gap = hits / trials

    metrics = {
        "task": "video_moderation",
        "fixed_1fps": {
            "ad_gap_detected": fixed_gap,
            "ad_hit_detected": fixed_hit,
            "normal_false_positive": fixed_normal,
        },
        "dense_0_4s": {"ad_gap_detection_rate": round(random_gap, 4), "trials": trials},
    }
    (WEIGHTS / "video_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
