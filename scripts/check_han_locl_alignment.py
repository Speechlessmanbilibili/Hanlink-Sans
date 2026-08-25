#!/usr/bin/env python3
"""区域字形行为验证（v1.3.0）：Hanlink vs Noto Sans SC / Noto CJK。

- zh-CN 与无语言：Hanlink 输出应 == GF 裁剪版 Noto Sans SC（SC 行为保留）
- zh-TW / ja / ko / zh-HK：Hanlink 输出应 == 四地合一 Noto CJK 同语言输出
  （区域变体轮廓一致）
"""
from pathlib import Path
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
HL = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "fonts/static/HanlinkSans-Regular.ttf"
SC = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "sources/noto/static/NotoSansSC-Regular.ttf"
CJK = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "sources/noto-cjk/static/NotoSansSC-Regular.ttf"

# 简/繁/日/韩/港写法不同的常用汉字
CHARS = (
    "骨直角戶户海雪青黒黑毎每社者験验発发関关広广対对帰归車车馬马鳥鸟無无"
    "為为國国廣广語语說说綠绿線线體体臺台湾湾裏里豐丰讀读聽听邊边還还進进"
    "過过這这樣样時时間间學学書书寫写畫画當当聞闻問问開开關关閉闭骨角直海"
    "門门電电話话號号點点龍龙風风雲云飛飞愛爱萬万禮礼歷历經经濟济嚴严實实"
)

_cache = {}
def shape(path, text, lang):
    key = (str(path), text, lang)
    if key not in _cache:
        face = hb.Face(open(path, "rb").read())
        font = hb.Font(face)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if lang:
            buf.language = lang
        hb.shape(font, buf, {})
        _cache[key] = [i.codepoint for i in buf.glyph_infos]
    return _cache[key]

_fonts = {}
def font_of(path):
    if path not in _fonts:
        _fonts[path] = TTFont(path)
    return _fonts[path]

def glyph_sig(path, gid):
    f = font_of(path)
    order = f.getGlyphOrder()
    name = order[gid] if gid < len(order) else None
    if name is None or name not in f["glyf"]:
        return ("?",)
    g = f["glyf"][name]
    if g.numberOfContours < 0:
        return ("c", tuple(sorted((c.glyphName,) for c in g.components)))
    coords, endpts, flags = g.getCoordinates(f["glyf"])
    return ("s", tuple(coords), tuple(endpts))

def main():
    fails = 0
    # 1) zh-CN：与 GF Noto Sans SC 对齐（SC 行为保留）
    for ch in CHARS:
        a = shape(HL, ch, "zh-CN")[0]
        b = shape(SC, ch, "zh-CN")[0]
        if glyph_sig(HL, a) != glyph_sig(SC, b):
            print(f"✗ zh-CN {ch}: 与 Noto SC 不一致")
            fails += 1
    print(f"[1] zh-CN 与 Noto Sans SC 对齐: {'✓' if fails == 0 else '✗'}")

    # 2) 区域语言：与四地合一 Noto CJK 对齐（变体正确）
    langs = {"zh-TW": "ZHT", "ja": "JAN", "ko": "KOR", "zh-HK": "ZHH"}
    total_ok = total_diff = 0
    for lang, tag in langs.items():
        ok = diff = 0
        for ch in CHARS:
            a = shape(HL, ch, "zh-CN")[0]
            b = shape(HL, ch, lang)[0]
            if a == b:
                continue  # 该字无变体
            c = shape(CJK, ch, lang)[0]
            if glyph_sig(HL, b) == glyph_sig(CJK, c):
                ok += 1
            else:
                diff += 1
                print(f"✗ {lang} {ch}: 变体轮廓与 Noto CJK 不一致")
                fails += 1
        print(f"[2] {lang} ({tag}): 变体生效 {ok}, 不一致 {diff}")
        total_ok += ok
        total_diff += diff
    print(f"\n总计: 变体生效 {total_ok}, 不一致 {total_diff}, 失败 {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
