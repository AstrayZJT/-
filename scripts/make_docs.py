"""把 docs/report.md 转成 Word，并生成答辩 PPT。

运行：python scripts/make_docs.py
依赖：python-docx、python-pptx（requirements-dev.txt）
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptRGB
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches as PInches
from pptx.util import Pt as PPt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SHOTS = DOCS / "screenshots"

INDIGO = RGBColor(0x5B, 0x5B, 0xD6)
DARK = RGBColor(0x1F, 0x23, 0x30)
GREY = RGBColor(0x7A, 0x81, 0x94)


# --------------------------------------------------------------------- docx
def set_cn_font(run, name: str = "宋体", size: int | None = None, bold: bool | None = None,
                color: RGBColor | None = None) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def add_inline(paragraph, text: str) -> None:
    parts = re.split(r"(\*\*.+?\*\*|`.+?`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            set_cn_font(run, bold=True)
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            set_cn_font(run, "Consolas", 9)
        else:
            run = paragraph.add_run(part)
            set_cn_font(run)


def style_document(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(4)

    for style_name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5)):
        style = doc.styles[style_name]
        style.font.name = "黑体"
        style.font.size = Pt(size)
        style.font.color.rgb = DARK
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)

    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.4)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.6)
    section.right_margin = Cm(2.6)


def cover(doc: Document) -> None:
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("应用综合实验")
    set_cn_font(run, "黑体", 22, True, GREY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("SocialSim 社交网络拟真平台")
    set_cn_font(run, "黑体", 30, True, DARK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("——面向内容安全的社交网络模拟与 AI 攻防实验")
    set_cn_font(run, "宋体", 14, False, GREY)

    for _ in range(5):
        doc.add_paragraph()

    for label, value in (
        ("课程名称", "应用综合实验"),
        ("实验题目", "社交网络拟真开发"),
        ("小组成员", "________（学号：________）"),
        ("", "________（学号：________）"),
        ("", "________（学号：________）"),
        ("指导教师", "________"),
        ("完成日期", "2026 年 11 月"),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{label}：{value}" if label else value)
        set_cn_font(run, "宋体", 12)

    doc.add_page_break()


def add_table(doc: Document, rows: list[list[str]]) -> None:
    if not rows:
        return
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j in range(cols):
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(2)
            text = row[j] if j < len(row) else ""
            run = p.add_run(text)
            set_cn_font(run, "宋体", 9, bold=(i == 0))
    doc.add_paragraph()


def parse_markdown(doc: Document, text: str) -> None:
    lines = text.splitlines()
    i = 0
    in_code = False
    code_buf: list[str] = []
    num = 0
    prev_numbered = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run("\n".join(code_buf))
                set_cn_font(run, "Consolas", 9)
                code_buf = []
                in_code = False
            else:
                in_code = True
            prev_numbered = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            prev_numbered = False
            i += 1
            continue

        if stripped.startswith("# "):
            prev_numbered = False
            i += 1
            continue

        if stripped.startswith("## "):
            doc.add_heading(stripped[3:].strip(), level=1)
            prev_numbered = False
            i += 1
            continue

        if stripped.startswith("### "):
            doc.add_heading(stripped[4:].strip(), level=2)
            prev_numbered = False
            i += 1
            continue

        if stripped.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
            if m:
                path = (DOCS / m.group(2)).resolve()
                if path.exists():
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(str(path), width=Inches(6.1))
                    cap = doc.add_paragraph()
                    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = cap.add_run(m.group(1))
                    set_cn_font(run, "宋体", 9, False, GREY)
            prev_numbered = False
            i += 1
            continue

        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in row):
                    rows.append(row)
                i += 1
            add_table(doc, rows)
            prev_numbered = False
            continue

        if stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, stripped[2:])
            prev_numbered = False
            i += 1
            continue

        if re.match(r"^\d+\.\s", stripped):
            num = num + 1 if prev_numbered else 1
            text_value = re.sub(r"^\d+\.\s+", "", stripped)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.74)
            p.paragraph_format.first_line_indent = Cm(-0.74)
            p.paragraph_format.line_spacing = 1.5
            run = p.add_run(f"{num}. ")
            set_cn_font(run, "宋体", 10.5)
            add_inline(p, text_value)
            prev_numbered = True
            i += 1
            continue

        # 普通段落：合并连续非空行
        buf = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(
            ("#", "|", "- ", "![", "```")
        ):
            buf.append(lines[i].strip())
            i += 1
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0.74)
        add_inline(p, "".join(buf))
        prev_numbered = False


def build_docx() -> Path:
    md = (DOCS / "report.md").read_text(encoding="utf-8")
    # 从摘要开始正文；封面单独构造
    body = md.split("## 摘要", 1)[1]
    body = "## 摘要" + body

    doc = Document()
    style_document(doc)
    cover(doc)
    parse_markdown(doc, body)

    # 页脚页码
    from docx.oxml import OxmlElement

    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()
    set_cn_font(run, "宋体", 9, False, GREY)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)

    out = DOCS / "报告-SocialSim.docx"
    doc.save(out)
    return out


# ---------------------------------------------------------------------- pptx
def _rgb(value) -> PptRGB:
    if isinstance(value, int):
        return PptRGB((value >> 16) & 255, (value >> 8) & 255, value & 255)
    return PptRGB(*value)


def ppt_text(slide, left, top, width, height, text, size=18, bold=False, color=DARK,
             align=PP_ALIGN.LEFT, font="微软雅黑"):
    box = slide.shapes.add_textbox(PInches(left), PInches(top), PInches(width), PInches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = PPt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)
    run.font.name = font
    return box


def ppt_bullets(slide, left, top, width, height, items, size=16, color=DARK):
    box = slide.shapes.add_textbox(PInches(left), PInches(top), PInches(width), PInches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = PPt(10)
        run = p.add_run()
        run.text = "• " + item
        run.font.size = PPt(size)
        run.font.color.rgb = _rgb(color)
        run.font.name = "微软雅黑"
    return box


def ppt_title(slide, title, subtitle=""):
    bar = slide.shapes.add_shape(1, PInches(0), PInches(0), PInches(13.333), PInches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = PptRGB(0x5B, 0x5B, 0xD6)
    bar.line.fill.background()
    ppt_text(slide, 0.7, 0.42, 11.5, 0.8, title, size=30, bold=True)
    if subtitle:
        ppt_text(slide, 0.72, 1.12, 11.5, 0.5, subtitle, size=14, color=0x7A8194)


def ppt_image(slide, path: Path, left, top, width=None, height=None):
    if not path.exists():
        return
    if width and height:
        slide.shapes.add_picture(str(path), PInches(left), PInches(top),
                                 width=PInches(width), height=PInches(height))
    elif width:
        slide.shapes.add_picture(str(path), PInches(left), PInches(top), width=PInches(width))
    else:
        slide.shapes.add_picture(str(path), PInches(left), PInches(top), height=PInches(height))


def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = PInches(13.333)
    prs.slide_height = PInches(7.5)
    blank = prs.slide_layouts[6]

    # 1 封面
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(1, PInches(0), PInches(0), PInches(13.333), PInches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = PptRGB(0x1D, 0x1C, 0x33)
    bg.line.fill.background()
    deco = s.shapes.add_shape(1, PInches(8.6), PInches(-1.2), PInches(6), PInches(6))
    deco.fill.solid()
    deco.fill.fore_color.rgb = PptRGB(0x5B, 0x5B, 0xD6)
    deco.line.fill.background()
    ppt_text(s, 0.9, 1.35, 9.5, 0.5, "应用综合实验 · 课程项目", size=15, color=0xB9B3FF)
    ppt_text(s, 0.9, 1.95, 9.8, 1.9, "SocialSim\n社交网络拟真平台", size=46, bold=True, color=0xFFFFFF)
    ppt_text(s, 0.95, 4.0, 9.8, 0.7, "水军模拟 · 多模态审核 · AI 攻防实验", size=22, color=0xD9D7F2)
    ppt_text(s, 0.95, 6.3, 9.8, 0.5, "西北工业大学 · 光电与智能研究院 · 2026", size=13, color=0x8E8BAE)

    # 2 背景与选题
    s = prs.slides.add_slide(blank)
    ppt_title(s, "题目与要求", "课程要求 3 人小组完成，交付代码、报告、PPT 与演示视频")
    ppt_bullets(s, 0.75, 1.75, 6.1, 4.8, [
        "基本功能：水军账号功能；长/短视频解析与不良内容监测",
        "扩展功能：结合 AI Security 对抗实例，做文本/图片/视频攻防",
        "加分项：软件著作权、算法创新",
        "课件参考：社交平台图像保护（加载—编辑—对抗—分享）",
    ], size=16)
    box = s.shapes.add_shape(1, PInches(7.1), PInches(1.9), PInches(5.4), PInches(3.6))
    box.fill.solid()
    box.fill.fore_color.rgb = PptRGB(0xF2, 0xF0, 0xFF)
    box.line.fill.background()
    ppt_text(s, 7.45, 2.15, 4.8, 0.5, "我们的定位", size=18, bold=True, color=0x5B5BD6)
    ppt_text(s, 7.45, 2.75, 4.7, 2.5,
             "一个能跑、能演、能讲清楚的原型：\n平台是载体，内容审核与攻防对比是重点。",
             size=17, color=0x1F2330)

    # 3 架构
    s = prs.slides.add_slide(blank)
    ppt_title(s, "系统架构", "单仓库、单端口交付；模型本地训练与推理，断网可演示")
    boxes = [
        (0.8, 1.8, 3.1, 1.0, "Vue3 + ECharts\n信息流 / 管理后台", 0x5B5BD6),
        (4.6, 1.8, 3.1, 1.0, "FastAPI\nJWT / 审核 / 调度", 0x6C5CE7),
        (8.4, 1.8, 3.9, 1.0, "SQLite + 本地媒体\n业务与实验记录", 0x0984E3),
        (1.6, 4.2, 3.0, 1.0, "文本：TF-IDF + LR\n关键词 / 归一化", 0x00B894),
        (5.2, 4.2, 3.0, 1.0, "图像：小型 CNN\n干净 / 对抗训练", 0xE17055),
        (8.8, 4.2, 3.0, 1.0, "视频：抽帧 + 聚合\n1fps / 0.4s", 0xD63031),
    ]
    for left, top, w, h, label, color in boxes:
        shp = s.shapes.add_shape(5, PInches(left), PInches(top), PInches(w), PInches(h))
        shp.fill.solid()
        shp.fill.fore_color.rgb = PptRGB((color >> 16) & 255, (color >> 8) & 255, color & 255)
        shp.line.fill.background()
        tf = shp.text_frame
        tf.word_wrap = True
        tf.text = label
        for p in tf.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = PPt(14)
                r.font.color.rgb = PptRGB(255, 255, 255)
                r.font.bold = True
                r.font.name = "微软雅黑"

    # 4 平台
    s = prs.slides.add_slide(blank)
    ppt_title(s, "社交平台：拟真的产品形态", "注册登录、图文/短视频、信息流、点赞评论关注、搜索、主页")
    ppt_bullets(s, 0.75, 1.8, 4.6, 4.6, [
        "信息流：最新 / 最热 / 搜索",
        "发帖：文字 + 图片 / 短视频上传",
        "互动：点赞、评论、关注",
        "审核状态：通过 / 待审 / 未通过",
        "演示账号：普通用户与管理员",
    ], size=15)
    ppt_image(s, SHOTS / "view-01-feed.png", 5.6, 1.55, width=7.2)

    # 5 水军
    s = prs.slides.add_slide(blank)
    ppt_title(s, "水军模拟：协同行为可编排、可观察", "批量建号、四种动作、任务进度与刷屏曲线")
    ppt_bullets(s, 0.75, 1.8, 4.6, 4.6, [
        "账号池：自动补齐 BOT，人设与资料",
        "动作：点赞 / 评论 / 关注 / 发帖",
        "编排：目标帖子、数量、间隔、时长",
        "观测：执行次数、1 秒桶时间曲线",
        "话术：同音字变体，用于攻防联动",
    ], size=15)
    ppt_image(s, SHOTS / "view-05-bots.png", 5.55, 1.55, width=7.25)

    # 6 审核
    s = prs.slides.add_slide(blank)
    ppt_title(s, "内容审核：三模态流水线", "模型初判 + 人工复核；每次处置留痕")
    ppt_bullets(s, 0.75, 1.8, 4.7, 4.6, [
        "文本：关键词 → 归一化 → 分类模型",
        "图片：CNN 识别广告图 / 二维码",
        "视频：抽帧 + 时序聚合，定位秒级区间",
        "队列：模态、标签、置信度、理由",
        "处置：通过 / 驳回，联动信息流",
    ], size=15)
    ppt_image(s, SHOTS / "view-04-moderation.png", 5.6, 1.55, width=7.2)

    # 7 文本攻防
    s = prs.slides.add_slide(blank)
    ppt_title(s, "文本攻防：同音字、零宽、拆分、Emoji", "同一段广告，在三种防线下的判定结果")
    ppt_image(s, SHOTS / "06a-lab-text-result.png", 0.55, 1.65, width=6.6)
    ppt_bullets(s, 7.5, 1.9, 5.2, 4.6, [
        "关键词基线：同音字绕过率 85.2%",
        "归一化：同音 0%，零宽 9.4%，拆分 25%",
        "分类模型：四类变体均为 0%",
        "Emoji 变体：归一化仍漏 88.3%，模型可拦",
    ], size=15)

    # 8 图像与视频
    s = prs.slides.add_slide(blank)
    ppt_title(s, "图像与视频：像素扰动与采样间隙", "PGD 让广告图被判为正常；1fps 漏掉 0.3 秒广告")
    ppt_image(s, SHOTS / "06b-lab-image-result.png", 0.55, 1.6, width=6.2)
    ppt_image(s, SHOTS / "06c-lab-video-result.png", 6.85, 1.6, width=6.0)
    ppt_text(s, 0.75, 6.55, 5.9, 0.5, "PGD ε=24/255：攻击成功率 50% → 对抗训练 3.3%", size=13, color=0x7A8194)
    ppt_text(s, 6.95, 6.55, 5.9, 0.5, "1fps 漏检；0.4s 密采样检出率 72.5%", size=13, color=0x7A8194)

    # 9 数据
    s = prs.slides.add_slide(blank)
    ppt_title(s, "实验结果", "合成数据、同分布测试；数字由脚本实际跑出")
    rows = [
        ("模块", "指标", "结果"),
        ("文本", "关键词 / 归一化 / 模型 准确率", "83.3% / 93.7% / 100%"),
        ("文本", "同音字绕过率（三级防线）", "85.2% / 0% / 0%"),
        ("图像", "PGD 攻击成功率（干净 / 对抗训练）", "50.0% / 3.3%"),
        ("视频", "1fps 漏检 → 0.4s 检出率", "漏检 / 72.5%"),
        ("系统", "单元测试 / 冒烟测试", "9/9 / 11/11"),
    ]
    table = s.shapes.add_table(len(rows), 3, PInches(0.8), PInches(1.9),
                               PInches(11.7), PInches(4.3)).table
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.text = value
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = PPt(14 if i else 15)
                    r.font.bold = i == 0
                    r.font.name = "微软雅黑"
                    r.font.color.rgb = PptRGB(255, 255, 255) if i == 0 else PptRGB(0x1F, 0x23, 0x30)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PptRGB(0x5B, 0x5B, 0xD6) if i == 0 else PptRGB(0xF7, 0xF7, 0xFB)

    # 10 演示
    s = prs.slides.add_slide(blank)
    ppt_title(s, "演示流程", "5 分钟讲完：正常使用 → 水军 → 审核 → 攻击 → 防御")
    steps = [
        ("01", "正常使用", "发帖、刷 feed、点赞评论"),
        ("02", "水军刷屏", "20 个 BOT 点赞评论，看曲线"),
        ("03", "审核拦截", "队列理由、置信度、通过/驳回"),
        ("04", "攻击绕过", "同音字、PGD、1fps 采样间隙"),
        ("05", "防御升级", "切到等级 2，重跑攻击看数据"),
    ]
    for idx, (num, title, desc) in enumerate(steps):
        left = 0.8 + idx * 2.45
        shp = s.shapes.add_shape(5, PInches(left), PInches(2.0), PInches(2.2), PInches(2.6))
        shp.fill.solid()
        shp.fill.fore_color.rgb = PptRGB(0xF2, 0xF0, 0xFF) if idx % 2 == 0 else PptRGB(0xE8, 0xF8, 0xF3)
        shp.line.fill.background()
        tf = shp.text_frame
        tf.word_wrap = True
        tf.text = f"{num}\n{title}\n{desc}"
        for p in tf.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.name = "微软雅黑"
                r.font.color.rgb = PptRGB(0x1F, 0x23, 0x30)

    # 11 总结
    s = prs.slides.add_slide(blank)
    ppt_title(s, "总结与改进", "完成了课程要求的基本功能与主要扩展功能")
    ppt_bullets(s, 0.8, 1.8, 5.8, 4.8, [
        "平台：图文/短视频 + 完整互动",
        "水军：批量建号、协同动作、可视化",
        "审核：文本/图片/视频三模态",
        "攻防：3 类攻击 + 3 类防御 + 量化",
        "测试：9 单元 + 11 冒烟 + 8 页面无报错",
    ], size=15)
    ppt_bullets(s, 7.0, 1.8, 5.7, 4.8, [
        "数据为合成、同分布，指标偏乐观",
        "后续：RoBERTa/CLIP、真实数据跨域测试",
        "后续：对抗贴纸、语音对抗、推荐投毒",
        "后续：水军协同检测算法（图 + 时序）",
    ], size=15)

    # 12 结束
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(1, PInches(0), PInches(0), PInches(13.333), PInches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = PptRGB(0x1D, 0x1C, 0x33)
    bg.line.fill.background()
    ppt_text(s, 0.9, 2.7, 11.5, 1.2, "谢谢，请老师和同学提问", size=40, bold=True, color=0xFFFFFF, align=PP_ALIGN.CENTER)
    ppt_text(s, 0.9, 4.0, 11.5, 0.6, "SocialSim · 源代码与实验数据见仓库", size=16,
             color=0xB9B3FF, align=PP_ALIGN.CENTER)

    out = DOCS / "答辩-SocialSim.pptx"
    prs.save(out)
    return out


if __name__ == "__main__":
    docx_path = build_docx()
    pptx_path = build_pptx()
    print("docx:", docx_path)
    print("pptx:", pptx_path)
