"""生成《SocialSim 项目汇报手册》Word 文档（复用 make_docs 的 Markdown 解析器）。"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))

from make_docs import GREY, set_cn_font, style_document, parse_markdown  # noqa: E402


def cover(doc: Document) -> None:
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("应用综合实验 · 课程项目")
    set_cn_font(run, "黑体", 16, True, GREY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("SocialSim\n社交网络拟真平台")
    set_cn_font(run, "黑体", 30, True, RGBColor(31, 35, 48))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("项目汇报手册")
    set_cn_font(run, "黑体", 26, True, RGBColor(91, 91, 214))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("给汇报同学的使用说明 · 10 分钟版")
    set_cn_font(run, "宋体", 14, False, GREY)

    for _ in range(4):
        doc.add_paragraph()

    for line in (
        "包含：项目一页纸 / 架构图 / 功能截图 / 审核原理",
        "10 分钟演示路径 / 汇报话术 / 20 个追问回答",
        "",
        "2026 年 11 月",
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        set_cn_font(run, "宋体", 12, False, RGBColor(60, 64, 80))

    doc.add_page_break()


def add_page_numbers(doc: Document) -> None:
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


def main() -> None:
    md = (DOCS / "briefing.md").read_text(encoding="utf-8")
    doc = Document()
    style_document(doc)
    # 手册页边距略小，给截图和示意图更多宽度
    section = doc.sections[0]
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    cover(doc)
    parse_markdown(doc, md, image_width=6.5)
    add_page_numbers(doc)
    out = DOCS / "汇报手册-SocialSim.docx"
    doc.save(out)
    print("docx:", out)


if __name__ == "__main__":
    main()
