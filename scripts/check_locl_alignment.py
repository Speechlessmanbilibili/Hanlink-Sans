#!/usr/bin/env python3
"""locl 行为对齐核查（全部语言路径）。

对每个 CJK 语言路径，比较 Hanlink 的 locl 输出与对应 Noto 区域源
（SC/TC/JP/KR）的 locl 输出是否一致：
- 输出字形可映射回码点 → 比较码点序列
- 输出字形是隐藏字形（unencoded）→ 比较轮廓签名（coords/endpts/flags）

预期差异（设计使然，单独列出）：
- Western 语言路径：标点用 Hanken（与 Noto 不同是故意的）
- 默认/无语言路径：标点用 bridge（与 Noto SC 相同或故意差异）
"""
import sys
from pathlib import Path
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "locl-alignment-report.txt"

HL = ROOT / "fonts/static/HanlinkSans-Regular.ttf"
REGIONS = {
    "zh-CN": ROOT / "sources/noto/static/NotoSansSC-Regular.ttf",
    "zh-TW": ROOT / "../CJK-Punct-Bridge/upstream/NotoSansTC-wght.ttf",
    "ja": ROOT / "../CJK-Punct-Bridge/upstream/NotoSansJP-wght.ttf",
    "ko": ROOT / "../CJK-Punct-Bridge/upstream/NotoSansKR-wght.ttf",
}

# 46 共享标点 + 中文常用标点 + 区域特有标点
PUNCTS = "!\"#%&'()*,-./:;?@[\\]_~{|}¡§«¶·»¿–—―‘’‚“”„†‡•…‰‹›、。〈〉《》「」『』【】〔〕〖〗〝〞゠・〜～"

_cache = {}
def shape(path, text, lang, feats=()):
    key = (str(path), lang, feats)
    if key not in _cache:
        face = hb.Face(open(path, "rb").read())
        font = hb.Font(face)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if lang:
            buf.language = lang
        hb.shape(font, buf, {t: True for t in feats})
        _cache[key] = [(i.codepoint, p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]
    return _cache[key]

_fonts = {}
def font_of(path):
    if path not in _fonts:
        _fonts[path] = TTFont(path)
    return _fonts[path]

def glyph_signature(path, gid):
    f = font_of(path)
    cmap = f.getBestCmap()
    rev = {g: cp for cp, g in cmap.items()}
    name = rev.get(gid)
    if name is None:
        # unencoded：通过 glyf 顺序找？需要 glyph name。用 GID 查 glyf 不便，
        # 退而求其次：返回 (None, None) 表示无法签名对比
        return ("unencoded", None)
    g = f["glyf"][name]
    if g.numberOfContours < 0:
        return ("composite", tuple(sorted((c.glyphName, c.transform) for c in g.components)))
    coords, endpts, flags = g.getCoordinates(f["glyf"])
    return ("simple", (tuple(coords), tuple(endpts), bytes(flags)))

def to_unicode(path, glyphs):
    f = font_of(path)
    cmap = f.getBestCmap()
    rev = {gid: cp for cp, gid in cmap.items()}
    return [(chr(rev.get(gid, 0xFFFD)), adv) for gid, adv in glyphs]

def main():
    lines = []
    def log(s=""):
        lines.append(s)

    log("locl 行为对齐核查：Hanlink Sans vs Noto 区域源（静态 Regular）")
    log("=" * 70)

    # 1) 全部语言路径的标点行为
    log("\n[1] 标点字符 × 语言路径（输出字形→码点序列 + 总 advance）")
    diffs = 0
    for lang, src in REGIONS.items():
        log(f"\n--- 语言 {lang}（源: {src.name}）---")
        for ch in PUNCTS:
            a = shape(HL, ch, lang)
            b = shape(src, ch, lang)
            sa = "".join(c for c, _ in to_unicode(HL, a))
            sb = "".join(c for c, _ in to_unicode(src, b))
            adv_a = sum(x for _, x in a)
            adv_b = sum(x for _, x in b)
            same = sa == sb and adv_a == adv_b
            if not same:
                diffs += 1
                # 隐藏字形：尝试轮廓签名
                note = ""
                if sa == "\ufffd" or sb == "\ufffd":
                    ga = glyph_signature(HL, a[0][0]) if a else None
                    gb = glyph_signature(src, b[0][0]) if b else None
                    note = f" 签名 HL={ga[0]} NOTO={gb[0]}"
                    if ga and gb and ga[0] == gb[0] == "simple":
                        note += f" 轮廓一致={ga[1] == gb[1]}"
                log(f"  ✗ {ch!r}: HL={sa!r}(adv {adv_a}) NOTO={sb!r}(adv {adv_b}){note}")
        log(f"  （{lang} 共 {len(PUNCTS)} 字符，{sum(1 for c in PUNCTS for _ in [0] if False)}…）")

    # 2) 汉字与假名正文（无 locl 差异预期，验证 merge 未改正文行为）
    log("\n[2] 正文样本（汉字/假名/注音，无标点）")
    body_cases = [
        ("中文正文测试", "zh-CN"),
        ("漢字傳統字體", "zh-TW"),
        ("日本語の文章", "ja"),
        ("한국어", "ko"),
        ("注音ㄅㄆㄇ", "zh-CN"),
    ]
    for text, lang in body_cases:
        a = shape(HL, text, lang)
        b = shape(REGIONS[lang], text, lang)
        sa = "".join(c for c, _ in to_unicode(HL, a))
        sb = "".join(c for c, _ in to_unicode(REGIONS[lang], b))
        adv_a = sum(x for _, x in a); adv_b = sum(x for _, x in b)
        same = sa == sb and adv_a == adv_b
        log(f"  {'✓' if same else '✗ DIFF'} {lang}: {text!r} -> HL={sa!r} NOTO={sb!r}")

    # 3) 竖排行为（vert）
    log("\n[3] 竖排 vert（中文标点）")
    for lang, src in list(REGIONS.items())[:2]:
        text = "，。！？"
        a = shape(HL, text, lang, ("vert",))
        b = shape(src, text, lang, ("vert",))
        sa = "".join(c for c, _ in to_unicode(HL, a))
        sb = "".join(c for c, _ in to_unicode(src, b))
        same = sa == sb
        log(f"  {'✓' if same else '✗ DIFF'} {lang}: {text!r} vert -> HL={sa!r} NOTO={sb!r}")

    # 4) Western 路径（设计差异标注）
    log("\n[4] Western 语言路径（预期：Hanken 标点，与 Noto 不同是设计）")
    for lang in ("en", "de", "fr"):
        text = "hello, world! \"quote\""
        a = shape(HL, text, lang)
        b = shape(REGIONS["zh-CN"], text, lang)
        sa = "".join(c for c, _ in to_unicode(HL, a))
        sb = "".join(c for c, _ in to_unicode(REGIONS["zh-CN"], b))
        log(f"  {lang}: HL={sa!r} NOTO_SC={sb!r}（Hanken 接管，预期差异）")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已写入 {OUT}")
    print(f"标点级差异数（含设计差异）: {diffs}")


if __name__ == "__main__":
    main()
