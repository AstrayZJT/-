"""用本机 Chrome 做无头截图与前端控制台检查。

运行前先启动后端。截图输出到 docs/screenshots/。
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def main() -> int:
    login = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"},
                       timeout=30, trust_env=False).json()
    token, user = login["access_token"], login["user"]
    auth = json.dumps({"token": token, "user": user}, ensure_ascii=False)

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        ctx.add_init_script(f"localStorage.setItem('socialsim_auth', {json.dumps(auth)});")
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)

        pages = [
            ("/", "01-feed.png"),
            ("/post/1", "02-post.png"),
            ("/admin/dashboard", "03-dashboard-admin.png"),
            ("/admin/moderation", "04-moderation.png"),
            ("/admin/bots", "05-bots.png"),
            ("/admin/lab", "06-lab.png"),
            ("/admin/settings", "07-settings.png"),
        ]
        for path, name in pages:
            page.goto(BASE + path, wait_until="networkidle")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(OUT / name), full_page=True)
            print("shot", name)

        # 实验室：文本结果
        page.goto(BASE + "/admin/lab", wait_until="networkidle")
        page.get_by_role("button", name="运行攻防对比").click()
        page.wait_for_timeout(4500)
        page.screenshot(path=str(OUT / "06a-lab-text-result.png"), full_page=True)
        print("shot 06a-lab-text-result.png")

        # 实验室：图片攻击结果
        page.get_by_role("button", name="图片对抗").click()
        page.get_by_role("button", name="广告图").click()
        page.get_by_role("button", name="生成对抗样本并对比").click()
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT / "06b-lab-image-result.png"), full_page=True)
        print("shot 06b-lab-image-result.png")

        # 实验室：视频抽帧结果
        page.get_by_role("button", name="视频抽帧").click()
        page.get_by_role("button", name="分析演示视频").click()
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT / "06c-lab-video-result.png"), full_page=True)
        print("shot 06c-lab-video-result.png")

        # 登录页单独用无痕上下文
        ctx2 = browser.new_context(viewport={"width": 1440, "height": 1000})
        page2 = ctx2.new_page()
        page2.on("pageerror", lambda e: errors.append(f"login pageerror: {e}"))
        page2.goto(BASE + "/login", wait_until="networkidle")
        page2.screenshot(path=str(OUT / "00-login.png"), full_page=True)
        print("shot 00-login.png")

        browser.close()

    print("errors:", len(errors))
    for e in errors[:20]:
        print(" -", e)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
