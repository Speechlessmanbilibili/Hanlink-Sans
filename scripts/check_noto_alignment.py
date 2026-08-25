#!/usr/bin/env python3
"""行为对齐核查：Hanlink Sans vs Noto Sans SC（CJK 源）。

对比同输入下 HarfBuzz 的排版结果（选中的字形序列 + advance），
区分「设计差异」（bridge 接管标点、Zhudou 破折号等故意行为）
与「意外偏差」（merge/兼容层引入的意外变化）。
"""
import sys
from pathlib import Path
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[1] if "__file__" in dir() else Path(".")
HANLINK = ROOT / "fonts/static/HanlinkSans-Regular.ttf"
NOTO = ROOT / "sources/noto/static/NotoSansSC-Regular.ttf"

# (文本, 语言, 特性, 说明, 预期)
CASES = [
    ("中文测试。", "zh-CN", (), "中文+句号", "same"),
    ("中文，标点：；！？", "zh-CN", (), "中文标点", "same"),
    ("「引号」『引号』（括号）【】", "zh-CN", (), "引号括号", "same"),
    ("省略号……", "zh-CN", (), "省略号", "same"),
    ("破折号——", "zh-CN", (), "连续破折号", "diff-dash"),   # Zhudou 连续破折号（设计差异）
    ("一——二", "zh-CN", (), "破折号上下文", "diff-dash"),
    ("假名かなカナ", "ja", (), "假名", "same"),
    ("注音ㄅㄆㄇㄈ", "zh-Bopo", (), "注音", "same"),
    ("俄语Русский", "ru", (), "西里尔", "same"),
    ("中文竖排", "zh-CN", ("vert",), "竖排 vert", "same"),
    ("中文竖排", "zh-CN", ("vrt2",), "竖排 vrt2", "same"),
    ("，。！？", "zh-CN", ("fwid",), "fwid", "same"),
    ("，。！？", "zh-CN", ("pwid",), "pwid", "same"),
    ("，。！？", "zh-CN", ("hwid",), "hwid", "same"),
    ("！！", "zh-CN", ("dlig",), "dlig 感叹号", "same"),
    ("１２３４５", "zh-CN", (), "全角数字", "same"),
    ("漢字測試", "zh-TW", (), "繁体字（正文）", "same"),
    ("中文。", "ja", (), "日文语境中文标点", "same"),
    ("test English", "en", (), "英文（Hanken 接管）", "diff-latin"),
    ("，。", "en", (), "英文语境中文标点", "diff-latin"),
    ("中文！？", "ko", (), "韩文语境", "same"),
]


def shape(path, text, lang, features):
    face = hb.Face(path.read_bytes())
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if lang is not None:
        buf.language = lang
    hb.shape(font, buf, {t: True for t in features})
    return [(i.codepoint, p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def glyphs_to_unicode(path, glyphs):
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    cmap = f.getBestCmap()
    rev = {gid: cp for cp, gid in cmap.items()}
    out = []
    for gid, adv in glyphs:
        cp = rev.get(gid)
        out.append((chr(cp) if cp else f"<gid{gid}>", adv))
    f.close()
    return out


def main():
    hl, nt = [], []
    for path, tag in ((HANLINK, "Hanlink"), (NOTO, "Noto")):
        if not path.exists():
            print(f"缺失: {path}")
            sys.exit(1)
    print(f"对比: {HANLINK.name} vs {NOTO.name}\n")
    issues = 0
    for text, lang, feats, note, expect in CASES:
        a = shape(HANLINK, text, lang, feats)
        b = shape(NOTO, text, lang, feats)
        ua = glyphs_to_unicode(HANLINK, a)
        ub = glyphs_to_unicode(NOTO, b)
        seq_a = "".join(c for c, _ in ua)
        seq_b = "".join(c for c, _ in ub)
        adv_a = sum(x for _, x in a)
        adv_b = sum(x for _, x in b)
        same = seq_a == seq_b and adv_a == adv_b
        status = "✓ 一致" if same else "✗ 差异"
        if not same:
            issues += 1
        print(f"[{status}] {note:12s} {text!r} lang={lang} feat={feats}")
        if not same:
            print(f"    Hanlink: {seq_a!r} adv={adv_a}")
            print(f"    Noto   : {seq_b!r} adv={adv_b}")
            print(f"    预期: {expect}")
    print(f"\n共 {len(CASES)} 组，{issues} 组有差异（其中设计差异应在预期中标注）")


if __name__ == "__main__":
    main()
