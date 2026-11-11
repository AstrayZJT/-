"""端到端冒烟测试：覆盖登录、信息流、审核、水军、攻防实验室。

运行前先启动后端：uvicorn backend.app.main:app --port 8000
运行：python scripts/smoke.py
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=60, trust_env=False)
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))
        print(("PASS" if ok else "FAIL"), name, detail)

    health = client.get("/api/health").json()
    check("health", health.get("status") == "ok", str(health))

    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    check("admin login", r.status_code == 200 and r.json()["user"]["is_admin"])
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    feed = client.get("/api/posts?size=5").json()
    check("feed", feed["total"] > 0 and len(feed["items"]) > 0, f"total={feed['total']}")

    stats = client.get("/api/admin/stats", headers=h).json()
    check("stats", stats["posts"] > 0 and stats["pending"] > 0, str(stats))

    queue = client.get("/api/admin/moderation?status=pending", headers=h).json()
    check("moderation queue", len(queue) > 0, f"pending={len(queue)}")

    text = client.post("/api/admin/lab/text", headers=h,
                       json={"text": "加微信 abc123 兼职日结，一天300"}).json()
    evaded = [v for v in text["variants"] if v["evaded"]]
    caught = [
        v for v in text["variants"]
        if v["evaded"] and (v["normalized"]["label"] != "normal" or v["robust"]["label"] != "normal")
    ]
    check("text attack", len(evaded) >= 2, f"evaded={len(evaded)}")
    check("text defense", len(caught) == len(evaded), f"caught={len(caught)}")

    sample = ROOT / "data" / "uploads" / "demo" / "sample_ad.jpg"
    with sample.open("rb") as f:
        img = client.post("/api/admin/lab/image", headers=h,
                          files={"file": ("sample_ad.jpg", f, "image/jpeg")},
                          data={"eps": "0.094"}).json()
    check("image attack", img["after"]["label"] == "normal",
          f"{img['before']['label']} -> {img['after']['label']}")

    vid = client.post("/api/admin/lab/video", headers=h, json={"rate": 1.0}).json()
    check("video 1fps miss", vid["fixed_detected"] is False)
    check("video dense hit", vid["dense_detected"] is True,
          f"dense={vid['dense']['violations']}")

    post_id = feed["items"][0]["id"]
    c = client.post("/api/admin/campaigns", headers=h, json={
        "name": "冒烟测试", "target_post_id": post_id, "bot_count": 5,
        "actions": "like,comment", "comment_text": "支持", "interval_ms": 200, "duration_s": 6,
    }).json()
    time.sleep(4)
    detail = client.get(f"/api/admin/campaigns/{c['id']}", headers=h).json()
    check("bot campaign", detail["actions_done"] > 0, f"done={detail['actions_done']} series={len(detail['series'])}")

    client.post(f"/api/admin/campaigns/{c['id']}/stop", headers=h)

    failed = [c for c in checks if not c[1]]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
