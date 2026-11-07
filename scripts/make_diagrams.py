"""生成汇报手册用的示意图（PIL 绘制，不依赖 matplotlib/graphviz）。"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

INDIGO = (91, 91, 214)
PURPLE = (140, 122, 230)
TEAL = (0, 184, 148)
RED = (255, 118, 117)
AMBER = (253, 203, 110)
DARK = (31, 35, 48)
MUTED = (122, 129, 148)
LIGHT = (244, 245, 248)
WHITE = (255, 255, 255)
PALE_INDIGO = (240, 237, 255)
PALE_TEAL = (232, 250, 244)
PALE_RED = (255, 236, 236)
PALE_AMBER = (255, 248, 230)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def canvas(w: int = 1600, h: int = 900, bg=WHITE) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), bg)
    return img, ImageDraw.Draw(img)


def text_block(d, x, y, w, lines, size=20, color=DARK, bold=False, align="center",
               gap=8, max_lines=None):
    f = font(size, bold)
    if max_lines:
        lines = lines[:max_lines]
    # 简单换行：超宽自动拆
    wrapped = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        cur = ""
        for ch in line:
            if d.textlength(cur + ch, font=f) <= w:
                cur += ch
            else:
                wrapped.append(cur)
                cur = ch
        wrapped.append(cur)
    total_h = len(wrapped) * (size + gap)
    cy = y + (0 if align == "center" else 0)
    for i, line in enumerate(wrapped):
        ty = cy + i * (size + gap)
        if align == "center":
            d.text((x + w / 2, ty), line, font=f, fill=color, anchor="ma")
        else:
            d.text((x, ty), line, font=f, fill=color, anchor="la")
    return total_h


def box(d, x, y, w, h, fill=WHITE, outline=INDIGO, width=3, radius=18):
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)


def arrow(d, p1, p2, color=MUTED, width=3, head=12, dash=False):
    x1, y1 = p1
    x2, y2 = p2
    d.line([p1, p2], fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    pts = [
        (x2, y2),
        (x2 - head * math.cos(ang - math.pi / 6), y2 - head * math.sin(ang - math.pi / 6)),
        (x2 - head * math.cos(ang + math.pi / 6), y2 - head * math.sin(ang + math.pi / 6)),
    ]
    d.polygon(pts, fill=color)


def title(d, main, sub=""):
    d.text((60, 42), main, font=font(38, True), fill=DARK, anchor="la")
    if sub:
        d.text((62, 96), sub, font=font(20), fill=MUTED, anchor="la")
    d.line([60, 136, 1540, 136], fill=(230, 232, 239), width=2)


def label(d, xy, text, color=MUTED, size=16, bg=None):
    f = font(size)
    x, y = xy
    if bg:
        tw = d.textlength(text, font=f)
        d.rounded_rectangle([x - 6, y - 4, x + tw + 6, y + size + 6], radius=6, fill=bg)
    d.text((x, y), text, font=f, fill=color, anchor="la")


# ---------------------------------------------------------------- 1 架构
def architecture():
    img, d = canvas(1600, 900, (250, 250, 253))
    title(d, "SocialSim 总体架构", "单仓库、单端口交付；模型本地训练、本地推理，断网可演示")

    # 浏览器
    box(d, 70, 300, 330, 170, PALE_INDIGO, INDIGO)
    text_block(d, 90, 320, 290, ["浏览器 / 手机 H5", "Vue3 + ECharts", "信息流 · 管理后台"], 20, DARK, True)
    text_block(d, 90, 405, 290, ["REST + JWT"], 16, MUTED)

    # FastAPI
    box(d, 520, 260, 470, 250, WHITE, INDIGO)
    text_block(d, 540, 280, 430, ["FastAPI 应用层"], 24, INDIGO, True)
    text_block(d, 540, 330, 430, ["routers: auth / posts / admin", "services: moderation / bot_engine / lab",
                                  "JWT 鉴权 · 审核流水线 · 任务调度"], 16, DARK, False, "left")

    # 存储
    box(d, 1150, 210, 360, 130, PALE_TEAL, TEAL)
    text_block(d, 1170, 230, 320, ["SQLite"], 22, DARK, True)
    text_block(d, 1170, 270, 320, ["业务表 · 审核任务 · 实验记录"], 15, MUTED)
    box(d, 1150, 390, 360, 130, PALE_AMBER, (230, 160, 40))
    text_block(d, 1170, 410, 320, ["本地媒体目录"], 22, DARK, True)
    text_block(d, 1170, 450, 320, ["图片 / 视频，经 /media 访问"], 15, MUTED)

    # 模型层
    models = [
        (100, "文本审核", ["字符 TF-IDF + LR", "关键词 / 归一化 / 模型"], PALE_INDIGO, INDIGO),
        (590, "图像审核", ["SmallCNN（96×96）", "干净 / PGD 对抗训练"], PALE_RED, RED),
        (1080, "视频审核", ["OpenCV 抽帧", "复用图像 CNN + 聚合"], PALE_TEAL, TEAL),
    ]
    for x, name, lines, fill, line in models:
        box(d, x, 650, 420, 150, fill, line)
        text_block(d, x + 20, 670, 380, [name], 22, DARK, True)
        text_block(d, x + 20, 712, 380, lines, 16, MUTED)

    # 连线
    arrow(d, (400, 385), (520, 385), INDIGO, 3)
    label(d, (435, 355), "HTTP", INDIGO, 14)
    arrow(d, (990, 330), (1150, 280), TEAL, 3)
    label(d, (1005, 270), "读写", TEAL, 14)
    arrow(d, (990, 450), (1150, 450), (230, 160, 40), 3)
    label(d, (1005, 420), "文件", (200, 140, 20), 14)
    # FastAPI 到三个模型
    for x in (310, 800, 1290):
        arrow(d, (755, 510), (x, 650), MUTED, 2)
    label(d, (700, 560), "调用", MUTED, 14)

    img.save(OUT / "architecture.png")


# ---------------------------------------------------------------- 2 审核流程
def moderation_flow():
    img, d = canvas(1600, 820, (250, 250, 253))
    title(d, "一条内容的审核流程", "发帖请求内同步执行；命中后进队列，人工复核后决定是否展示")

    box(d, 50, 330, 210, 140, WHITE, INDIGO)
    text_block(d, 65, 350, 180, ["POST /api/posts"], 18, DARK, True)
    text_block(d, 65, 395, 180, ["文本 + 图片/视频"], 15, MUTED)

    box(d, 320, 300, 250, 200, PALE_INDIGO, INDIGO)
    text_block(d, 335, 320, 220, ["moderate_post()"], 20, INDIGO, True)
    text_block(d, 335, 365, 220, ["读取防御等级", "按模态分别审核", "合并优先级"], 15, DARK)

    box(d, 640, 160, 300, 110, PALE_INDIGO, INDIGO)
    text_block(d, 655, 180, 270, ["文本审核"], 20, DARK, True)
    text_block(d, 655, 215, 270, ["关键词 / 归一化 / 模型"], 15, MUTED)
    box(d, 640, 310, 300, 110, PALE_RED, RED)
    text_block(d, 655, 330, 270, ["图片审核"], 20, DARK, True)
    text_block(d, 655, 365, 270, ["CNN：ad / normal"], 15, MUTED)
    box(d, 640, 460, 300, 110, PALE_TEAL, TEAL)
    text_block(d, 655, 480, 270, ["视频审核"], 20, DARK, True)
    text_block(d, 655, 515, 270, ["抽帧 + 逐帧 CNN"], 15, MUTED)

    box(d, 1020, 300, 260, 200, WHITE, PURPLE)
    text_block(d, 1035, 320, 230, ["ModerationTask"], 18, PURPLE, True)
    text_block(d, 1035, 360, 230, ["每个模态一条记录", "pending / approved", "标签 · 分数 · 理由"], 14, DARK)

    box(d, 1020, 560, 260, 150, PALE_AMBER, (230, 160, 40))
    text_block(d, 1035, 580, 230, ["人工审核队列"], 19, DARK, True)
    text_block(d, 1035, 620, 230, ["通过 / 驳回，按帖子统一处置"], 14, MUTED)

    box(d, 1340, 330, 200, 140, PALE_TEAL, TEAL)
    text_block(d, 1355, 350, 170, ["信息流"], 20, DARK, True)
    text_block(d, 1355, 390, 170, ["只展示 approved"], 14, MUTED)

    arrow(d, (260, 400), (320, 400), INDIGO, 3)
    for y in (215, 365, 515):
        arrow(d, (570, 400), (640, y + 55), MUTED, 2)
    for y in (270, 420, 570):
        arrow(d, (940, y), (1020, 400 if y != 570 else 400), MUTED, 2)
    arrow(d, (1150, 500), (1150, 560), PURPLE, 3)
    label(d, (1160, 515), "复核", PURPLE, 14)
    arrow(d, (1280, 400), (1340, 400), TEAL, 3)
    label(d, (1290, 372), "通过", TEAL, 14)
    arrow(d, (1150, 560), (1150, 640), (230, 160, 40), 3) if False else None

    img.save(OUT / "moderation-flow.png")


# ---------------------------------------------------------------- 3 文本三级
def text_defense():
    img, d = canvas(1600, 720, (250, 250, 253))
    title(d, "文本审核的三级防线", "同一段广告，在三种策略下的判定结果（数字为实际运行结果）")

    panels = [
        (60, "等级 0 · 关键词基线", "伽薇信 abc123 兼 职 曰结", "正常 · 漏过", RED, PALE_RED),
        (560, "等级 1 · 归一化 + 关键词", "加微信 abc123 兼职日结", "广告 · 0.85", (230, 160, 40), PALE_AMBER),
        (1060, "等级 2 · 归一化 + 模型", "加微信 abc123 兼职日结", "广告 · 0.998", TEAL, PALE_TEAL),
    ]
    for x, head, sample, result, color, fill in panels:
        box(d, x, 180, 460, 420, WHITE, color, 3)
        d.text((x + 30, 205), head, font=font(21, True), fill=color, anchor="la")
        d.text((x + 30, 260), "输入", font=font(14, True), fill=MUTED, anchor="la")
        text_block(d, x + 30, 288, 400, [sample], 19, DARK, True, "left")
        d.text((x + 30, 380), "处理", font=font(14, True), fill=MUTED, anchor="la")
        proc = {
            0: "子串匹配：微信/兼职/日结 均未命中",
            1: "薇信→微信，兼 职→兼职，曰结→日结",
            2: "归一化后 → TF-IDF → 线性模型",
        }[panels.index((x, head, sample, result, color, fill))]
        text_block(d, x + 30, 408, 400, [proc], 15, DARK, False, "left")
        d.rounded_rectangle([x + 30, 500, x + 250, 560], radius=12, fill=fill)
        d.text((x + 140, 518), result, font=font(20, True), fill=color, anchor="ma")

    # 底部说明
    text_block(d, 80, 630, 1440,
               ["结论：关键词基线只能覆盖字符原样；归一化把变体还原；模型兜住 Emoji 等归一化去不掉的改写。"],
               15, MUTED)

    img.save(OUT / "text-three-levels.png")


# ---------------------------------------------------------------- 4 视频采样
def video_sampling():
    W, H = 1600, 720
    img, d = canvas(W, H, (250, 250, 253))
    title(d, "视频审核：为什么 1fps 会漏掉 0.3 秒的广告", "演示视频 8 秒；广告画面 4.65s–4.95s；抽帧点决定能不能抓到")

    left, right = 120, 1480
    y = 360
    d.line([left, y, right, y], fill=DARK, width=3)
    # 秒刻度
    for t in range(9):
        x = left + (right - left) * t / 8
        d.line([x, y - 8, x, y + 8], fill=DARK, width=2)
        d.text((x, y + 14), f"{t}s", font=font(15), fill=MUTED, anchor="ma")

    # 广告窗口
    x1 = left + (right - left) * 4.65 / 8
    x2 = left + (right - left) * 4.95 / 8
    d.rectangle([x1, y - 150, x2, y - 20], fill=(255, 220, 220), outline=RED, width=2)
    d.text(((x1 + x2) / 2, y - 185), "广告画面 0.3s", font=font(17, True), fill=RED, anchor="ma")
    d.text(((x1 + x2) / 2, y - 158), "4.65–4.95s", font=font(14), fill=RED, anchor="ma")

    # 1fps 采样（上方）
    for t in range(8):
        x = left + (right - left) * t / 8
        d.ellipse([x - 8, y - 22, x + 8, y - 6], fill=INDIGO)
        d.text((x, y - 54), f"{t}", font=font(14), fill=INDIGO, anchor="ma")
        if t in (4, 5):
            d.text((x, y - 78), "×", font=font(22, True), fill=RED, anchor="ma")
    d.text((120, 250), "固定 1fps 采样点：4.0s 和 5.0s 都落在广告窗口外", font=font(18, True), fill=INDIGO, anchor="la")

    # 0.4s 采样（下方）
    t = 0.0
    hit_x = None
    while t <= 8.001:
        x = left + (right - left) * t / 8
        if 4.65 <= t <= 4.95:
            d.ellipse([x - 9, y + 26, x + 9, y + 44], fill=TEAL)
            d.text((x, y + 54), f"{t:.1f}", font=font(13, True), fill=TEAL, anchor="ma")
            hit_x = x
        else:
            d.ellipse([x - 4, y + 30, x + 4, y + 38], fill=MUTED)
        t = round(t + 0.4, 1)
    if hit_x:
        d.text((hit_x, y + 92), "4.8s 命中", font=font(18, True), fill=TEAL, anchor="ma")
    d.text((120, 500), "0.4s 密采样：采样点落进窗口，检出广告（实测检出率 72.5%）", font=font(18, True), fill=TEAL, anchor="la")

    # 图例
    d.ellipse([120, 610, 136, 626], fill=INDIGO)
    d.text((146, 608), "1fps 采样点", font=font(15), fill=DARK, anchor="la")
    d.ellipse([300, 610, 316, 626], fill=TEAL)
    d.text((326, 608), "0.4s 采样点", font=font(15), fill=DARK, anchor="la")
    d.rectangle([480, 608, 500, 624], fill=(255, 220, 220), outline=RED)
    d.text((510, 608), "违规画面窗口", font=font(15), fill=DARK, anchor="la")

    img.save(OUT / "video-sampling.png")


# ---------------------------------------------------------------- 5 水军流程
def bot_flow():
    img, d = canvas(1600, 680, (250, 250, 253))
    title(d, "水军模拟的执行链路", "任务配置 → 协程调度 → 四类动作 → 数据看板")

    steps = [
        (60, "任务配置", ["目标帖子", "BOT 数量", "动作 / 间隔 / 时长"], PALE_INDIGO, INDIGO),
        (360, "asyncio 调度", ["按间隔轮询", "循环选择 BOT", "可随时停止"], PALE_TEAL, TEAL),
        (660, "四类动作", ["点赞 / 评论", "关注 / 发帖"], PALE_AMBER, (230, 160, 40)),
        (960, "写库与计数", ["bot_actions", "actions_done", "时间序列"], WHITE, PURPLE),
        (1260, "数据看板", ["执行次数", "刷屏曲线", "任务状态"], PALE_RED, RED),
    ]
    for x, head, lines, fill, color in steps:
        box(d, x, 300, 250, 200, fill, color)
        d.text((x + 25, 320), head, font=font(19, True), fill=color, anchor="la")
        for i, line in enumerate(lines):
            d.text((x + 25, 365 + i * 28), line, font=font(15), fill=DARK, anchor="la")

    for i in range(len(steps) - 1):
        arrow(d, (steps[i][0] + 250, 400), (steps[i + 1][0], 400), MUTED, 3)

    text_block(d, 80, 590, 1440,
               ["BOT 发帖会走同一条审核流水线：等级 0 时变体广告能进信息流，等级 2 时被模型拦截。"],
               15, MUTED)

    img.save(OUT / "bot-flow.png")


if __name__ == "__main__":
    architecture()
    moderation_flow()
    text_defense()
    video_sampling()
    bot_flow()
    print("diagrams written to", OUT)
