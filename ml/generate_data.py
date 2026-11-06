"""生成课程演示用的合成数据：文本、图片与短视频。

所有素材均为脚本合成，不含真实用户数据或真实不良内容。
运行：python ml/generate_data.py
"""

from __future__ import annotations

import csv
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed"
DEMO = ROOT / "data" / "demo"
for p in (SEED, DEMO):
    p.mkdir(parents=True, exist_ok=True)

random.seed(20261106)
np.random.seed(20261106)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------- text data
NORMAL_TEMPLATES = [
    "今天天气真好，去操场走了两圈",
    "食堂的牛肉面又涨价了，吃不起了",
    "图书馆三楼空调太冷，记得带外套",
    "周末去秦岭爬山，风景真不错",
    "刚交完实验报告，终于可以睡个好觉",
    "有人晚上一起打羽毛球吗",
    "新买的耳机音质一般，准备退了",
    "组会开到十点，人都麻了",
    "校门口新开了一家奶茶店，排队人很多",
    "求推荐一门好过的选修课",
    "今天代码跑通了，庆祝一下",
    "宿舍楼下的猫又胖了一圈",
    "早八真的起不来，谁懂",
    "最近在学强化学习，头有点大",
    "操场跑步五公里，配速终于进六了",
    "食堂新出的麻辣香锅味道不错",
    "实验室的服务器又崩了",
    "晚上去看了一场电影，还不错",
    "西安的秋天很短，抓紧拍照",
    "和室友一起做了顿火锅",
]

AD_TEMPLATES = [
    "加微信 {wx} 兼职日结，一天300",
    "低价出二手自行车，加V详聊",
    "扫码进群领资料，名额有限",
    "专业代写课程设计，价格美丽，加微信",
    "日结兼职，动动手指就能赚钱，加微信",
    "出售考研资料，联系QQ {qq}",
    "刷单返利，先到先得，加微信",
    "推广：点击链接领取优惠券",
    "招校园代理，零门槛，加薇信",
    "高薪兼职，日入500，私聊",
    "客服退款请加QQ {qq} 办理",
    "中奖了，先交手续费即可领取",
    "代刷网课，包过，加微信",
    "低价代购，正品保证，加V",
    "兼职打字员，日结200，加微信",
    "免费领取学习资料，扫码进群",
]

ABUSE_TEMPLATES = [
    "你就是个傻X",
    "滚开，别烦我",
    "垃圾东西，闭嘴",
    "这种人真恶心",
    "去死吧",
    "脑子有病吧",
    "废物一个，什么都干不成",
    "你算什么东西",
    "闭嘴吧，蠢货",
    "看见你就烦，滚",
    "就你这水平也好意思发出来",
    "别在这丢人现眼了",
]

SUFFIXES = ["", "！", "。", "…", " 急", " 在线等", " 真的", " 兄弟们", " 😅", " ！！！"]


def fill(t: str) -> str:
    return t.format(
        wx=random.choice(["abc123", "zs888", "wxid_9k2", "kk2026"]),
        qq=random.choice(["12345678", "987654321", "55667788"]),
    )


def make_text_rows(templates: list[str], label: str, n: int, offset: int = 0):
    rows = []
    for i in range(n):
        t = fill(templates[(i + offset) % len(templates)])
        rows.append({"label": label, "text": t + random.choice(SUFFIXES)})
    return rows


def build_text() -> None:
    # 分层随机切分：每个类别 80% 训练 / 20% 测试。
    # 说明：这是同分布测试集，用来观察“变体攻击”带来的性能变化，
    # 不用于宣称跨模板泛化能力。
    rng = random.Random(7)
    train, test = [], []
    for templates, label in (
        (NORMAL_TEMPLATES, "normal"),
        (AD_TEMPLATES, "ad"),
        (ABUSE_TEMPLATES, "abuse"),
    ):
        rows = make_text_rows(templates, label, 450)
        rng.shuffle(rows)
        cut = int(len(rows) * 0.8)
        train += rows[:cut]
        test += rows[cut:]

    rng.shuffle(train)
    rng.shuffle(test)
    with (SEED / "text_train.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["label", "text"])
        w.writeheader()
        w.writerows(train)
    with (SEED / "text_test.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["label", "text"])
        w.writeheader()
        w.writerows(test)
    print(f"text: train={len(train)} test={len(test)}")


# --------------------------------------------------------------- image data
IMG_SIZE = 96


def normal_image(size: int = IMG_SIZE) -> Image.Image:
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    c1 = np.array([random.randint(30, 200) for _ in range(3)], dtype=np.float32)
    c2 = np.array([random.randint(30, 220) for _ in range(3)], dtype=np.float32)
    for y in range(size):
        t = y / size
        arr[y, :, :] = (c1 * (1 - t) + c2 * t).astype(np.uint8)
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    for _ in range(random.randint(2, 5)):
        x0, y0 = random.randint(0, size - 20), random.randint(0, size - 20)
        x1, y1 = x0 + random.randint(8, 40), y0 + random.randint(8, 40)
        color = tuple(random.randint(0, 255) for _ in range(3))
        if random.random() < 0.5:
            d.ellipse([x0, y0, x1, y1], fill=color)
        else:
            d.rectangle([x0, y0, x1, y1], fill=color)
    noise = np.random.normal(0, 6, (size, size, 3))
    arr = np.clip(np.asarray(img).astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


AD_TEXTS = [
    ("限时特价", "加微信 abc123"),
    ("兼职日结", "日入300 加V"),
    ("扫码进群", "领学习资料"),
    ("低价代购", "QQ 12345678"),
    ("刷单返利", "加微信 zs888"),
    ("校园代理", "零门槛 高佣金"),
]


def ad_image(size: int = IMG_SIZE) -> Image.Image:
    bg = random.choice([(255, 230, 120), (255, 120, 90), (255, 250, 240), (180, 240, 200)])
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    title, sub = random.choice(AD_TEXTS)
    d.rectangle([2, 2, size - 3, size - 3], outline=(220, 30, 30), width=3)
    d.text((8, 10), title, font=get_font(20), fill=(200, 20, 20))
    d.text((8, 44), sub, font=get_font(12), fill=(30, 30, 30))
    d.text((8, 66), "点击咨询", font=get_font(12), fill=(30, 30, 90))
    if random.random() < 0.5:
        # 画一个二维码占位块（这不是可扫描的真实二维码，只是视觉元素）
        qx, qy = size - 34, size - 34
        for i in range(6):
            for j in range(6):
                if random.random() < 0.5:
                    d.rectangle([qx + i * 5, qy + j * 5, qx + i * 5 + 4, qy + j * 5 + 4], fill=(0, 0, 0))
    noise = np.random.normal(0, 3, (size, size, 3))
    arr = np.clip(np.asarray(img).astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def build_images() -> None:
    for split, n in (("train", 360), ("test", 90)):
        for label, fn in (("normal", normal_image), ("ad", ad_image)):
            out = SEED / "images" / split / label
            out.mkdir(parents=True, exist_ok=True)
            for i in range(n):
                fn().save(out / f"{label}_{i:04d}.jpg", quality=92)
    print("images: train=720 test=180")


# --------------------------------------------------------------- video demo
def _frame(text_lines: list[str], bg: tuple[int, int, int], size=(640, 360)) -> np.ndarray:
    w, h = size
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    y = 80
    for line, font_size, color in text_lines:
        d.text((40, y), line, font=get_font(font_size), fill=color)
        y += font_size + 26
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def _poster_frame(text_lines: list[str], bg: tuple[int, int, int], size=(640, 360)) -> np.ndarray:
    """画一张与训练集广告图风格一致的“海报帧”。"""
    w, h = size
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, w - 7, h - 7], outline=(220, 30, 30), width=7)
    y = 56
    for line, font_size, color in text_lines:
        d.text((40, y), line, font=get_font(font_size), fill=color)
        y += font_size + 26
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def _write_video(path: Path, frames: list[np.ndarray], fps: int = 24) -> None:
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
    for f in frames:
        writer.write(f)
    writer.release()


def build_videos() -> None:
    fps = 24
    seconds = 8
    normal_frames = [
        _frame([("校园 VLOG", 40, (30, 30, 30)), ("今天去操场跑步", 24, (60, 60, 60))], (210, 230, 245))
        for _ in range(fps * seconds)
    ]
    _write_video(DEMO / "normal.mp4", normal_frames, fps)

    ad = _poster_frame(
        [("兼职日结 日入300", 54, (200, 20, 20)), ("加微信 abc123", 40, (20, 20, 20)),
         ("名额有限 扫码咨询", 28, (20, 20, 120))],
        (255, 235, 130),
    )
    # 违规画面出现在 4.65s - 4.95s，1fps 的整数秒采样会整段跳过
    gap_frames = []
    for i in range(fps * seconds):
        t = i / fps
        gap_frames.append(ad if 4.65 <= t < 4.95 else normal_frames[i])
    _write_video(DEMO / "ad_gap.mp4", gap_frames, fps)

    # 对照组：违规画面正好落在整数秒，1fps 也能抓到
    hit = []
    for i in range(fps * seconds):
        t = i / fps
        hit.append(ad if 3.0 <= t < 3.3 else normal_frames[i])
    _write_video(DEMO / "ad_hit.mp4", hit, fps)

    # 同时放进上传目录，便于前端直接通过 /media/demo/... 播放
    upload_demo = ROOT / "data" / "uploads" / "demo"
    upload_demo.mkdir(parents=True, exist_ok=True)
    for name in ("normal.mp4", "ad_gap.mp4", "ad_hit.mp4"):
        shutil.copyfile(DEMO / name, upload_demo / name)
    print("videos: normal.mp4 ad_gap.mp4 ad_hit.mp4")


if __name__ == "__main__":
    build_text()
    build_images()
    build_videos()
