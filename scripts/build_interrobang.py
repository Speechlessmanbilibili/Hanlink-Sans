#!/usr/bin/env python3
"""Hanlink ?! —— Hanlink Sans 的 interrobang 连字变体构建。

从审计过的 Hanlink Sans v1.2 静态字体出发（输入：HANLINK_STATIC_DIR，默认
fonts/static），在每权重：
1. 合成 ?! -> ‽（半角，经典叠加）与 ？！-> 全宽 ‽
2. 从 Hanken VF 的相同字重提取 T_h，并挂 T+h -> T_h 到 liga（默认开启）
3. ?!/？！ 连字也挂 liga
4. 设置家族名 Hanlink ?! / PS HanlinkSansInterrobang / 斜体样式位
5. 输出 fonts/static/HanlinkSansInterrobang-{Style}.ttf，
   HANLINK_ITALIC=1 时从真实斜体源生成 *Italic.ttf

可变字体由 build_variable_interrobang.py 从这 9 个静态 master 构建。
"""
from array import array
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import os
from fontTools.misc.roundTools import otRound
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.otlLib.builder import buildLookup, buildLigatureSubstSubtable
from fontTools.otlLib.builder import buildStatTable
from fontTools.varLib.instancer import instantiateVariableFont
from font_metadata import (
    COPYRIGHT, DESIGNER, TRADEMARK, apply_binary_metadata, project_names,
)

REPO = Path(__file__).resolve().parents[1]
STATIC_IN = Path(os.environ.get("HANLINK_STATIC_DIR", REPO / "fonts" / "static"))
HANKEN_VF = Path(os.environ.get("HANKEN_VF_DIR", REPO / "sources" / "hanken"))
OUT = REPO / "fonts-interrobang" / "static"
OUT.mkdir(parents=True, exist_ok=True)

FAMILY = "Hanlink ?!"
PS = "HanlinkSansInterrobang"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
ITALIC = os.environ.get("HANLINK_ITALIC") == "1"
INTER_DEFAULT = REPO / "sources" / "inter" / (
    "InterVariable-Italic.ttf" if ITALIC else "InterVariable.ttf"
)
INTER_VF = Path(os.environ.get("INTER_VF", INTER_DEFAULT))
INTER_SHA256 = {
    False: "4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf",
    True: "d6f1f6a172d9e588438db9f986fd5cfad7b30f644374080a8a9d4d91e344586f",
}
INTER_LEGAL = {
    0: COPYRIGHT + " Portions Copyright 2016 The Inter Project Authors.",
    7: TRADEMARK + " Inter UI and Inter is a trademark of rsms.",
    9: DESIGNER + "; Rasmus Andersson (Inter).",
    10: "Hanlink ?! is a ligature variant of Hanlink Sans. "
        "Question mark + exclamation mark form an interrobang (U+203D and a full-width form); "
        "T+h forms the optional Th ligature, enabled by default.",
    11: "https://github.com/Speechlessmanbilibili/Hanlink-Sans",
}


def setname(font, nid, val):
    nt = font["name"]
    nt.names = [r for r in nt.names if r.nameID != nid]
    nt.setName(val, nid, 3, 1, 0x409)
    try:
        val.encode("mac_roman")
        nt.setName(val, nid, 1, 0, 0)
    except Exception:
        pass


def set_names(font, weight, style):
    nt = font["name"]
    italic = ITALIC
    if italic:
        sub = "Italic" if weight == 400 else f"{style} Italic"
        legacy_family = FAMILY if weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = "Bold Italic" if weight == 700 else "Italic"
        full = (FAMILY if weight == 400 else f"{FAMILY} {style}") + " Italic"
        unique = f"{PS}-Italic" if weight == 400 else f"{PS}-{style}Italic"
    else:
        sub = "Bold" if weight == 700 else "Regular"
        legacy_family = FAMILY if weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = sub
        full = FAMILY if weight == 400 else f"{FAMILY} {style}"
        unique = f"{PS}-{style}"
    vals = {**project_names(unique), **INTER_LEGAL,
            1: legacy_family, 2: legacy_sub,
            4: full, 6: unique,
            16: FAMILY, 17: (sub if italic else style), 25: PS}
    for k, v in vals.items():
        setname(font, k, v)
    o = font["OS/2"]
    o.usWeightClass = weight
    apply_binary_metadata(font)
    fs = o.fsSelection
    for bit in (0, 5, 6, 9):
        fs &= ~(1 << bit)
    if italic:
        fs |= 1 << 0
    if weight == 400 and not italic:
        fs |= 1 << 6
    if weight == 700:
        fs |= 1 << 5
    o.fsSelection = fs
    font["head"].macStyle &= ~3
    if weight == 700:
        font["head"].macStyle |= 1
    if italic:
        font["head"].macStyle |= 2


def validate_inter_source():
    if not INTER_VF.exists():
        raise SystemExit(f"缺少 Inter 源（U+203D 字形）: {INTER_VF}，请设置 INTER_VF")
    digest = sha256(INTER_VF.read_bytes()).hexdigest()
    if digest != INTER_SHA256[ITALIC]:
        raise SystemExit(
            f"Inter 源 SHA-256 不匹配: {digest}\n期望: {INTER_SHA256[ITALIC]}\n{INTER_VF}"
        )
    source = TTFont(INTER_VF, lazy=True)
    axes = {axis.axisTag: (axis.minValue, axis.defaultValue, axis.maxValue)
            for axis in source["fvar"].axes}
    if axes.get("wght") != (100.0, 400.0, 900.0) or "opsz" not in axes:
        raise SystemExit(f"Inter 源轴不符合预期: {axes}")
    if 0x203D not in source.getBestCmap():
        raise SystemExit("Inter 源没有 U+203D 字形")
    source.close()
    print(f"verified Inter source {INTER_VF.name} {digest}", flush=True)


def import_interrobang(font, weight):
    """从 Inter 提取 U+203D 字形（半宽）与全宽版（同轮廓，advance 1000 靠左）。

    全宽与半宽只差两侧留白，字形轮廓相同；全宽按中文全角惯例靠左，
    右侧留白。直接提取源字形坐标并缩放，不经过 pen（避免懒加载污染）。
    """
    variable = TTFont(INTER_VF)
    src = instantiateVariableFont(
        variable, {"opsz": 14, "wght": weight},
        inplace=False, optimize=True, static=True,
    )
    variable.close()
    glyph_name = src.getBestCmap()[0x203D]
    scale = 1000 / src["head"].unitsPerEm
    g = src["glyf"][glyph_name]
    coords, endpts, flags = g.getCoordinates(src["glyf"])
    new_coords = [(otRound(x * scale), otRound(y * scale)) for x, y in coords]
    new = Glyph()
    new.numberOfContours = g.numberOfContours
    new.coordinates = GlyphCoordinates(new_coords)
    new.endPtsOfContours = list(endpts)
    new.flags = array("B", flags)
    new.program = ttProgram.Program()
    new.recalcBounds(font["glyf"])
    adv_half = otRound(src["hmtx"].metrics[glyph_name][0] * scale)
    xmin = getattr(new, "xMin", 0)
    font["glyf"]["interrobang.uni203D"] = new
    font["hmtx"].metrics["interrobang.uni203D"] = (adv_half, xmin)
    font["glyf"]["interrobang.full"] = deepcopy(new)
    font["hmtx"].metrics["interrobang.full"] = (1000, xmin)  # 全宽靠左
    for n in ("interrobang.uni203D", "interrobang.full"):
        if "vmtx" in font:
            font["vmtx"].metrics[n] = (1000, 0)
    src.close()
    return ["interrobang.uni203D", "interrobang.full"]


def import_hanken_ligature(font, source, glyph_name):
    glyph = source["glyf"][glyph_name]
    coords, end_points, flags = glyph.getCoordinates(source["glyf"])
    scale = font["head"].unitsPerEm / source["head"].unitsPerEm
    imported = Glyph()
    imported.numberOfContours = len(end_points)
    imported.coordinates = GlyphCoordinates([
        (otRound(x * scale), otRound(y * scale)) for x, y in coords
    ])
    imported.endPtsOfContours = list(end_points)
    imported.flags = array("B", flags)
    imported.program = ttProgram.Program()
    imported.recalcBounds(font["glyf"])
    advance = otRound(source["hmtx"].metrics[glyph_name][0] * scale)
    font["glyf"][glyph_name] = imported
    font["hmtx"].metrics[glyph_name] = (advance, imported.xMin)
    if "vmtx" in font:
        font["vmtx"].metrics[glyph_name] = (1000, 0)


def build_weight(weight, style):
    src_path = STATIC_IN / (f"HanlinkSans-Italic.ttf" if (ITALIC and weight == 400) else
                            f"HanlinkSans-{style}{'Italic' if ITALIC else ''}.ttf")
    font = TTFont(src_path)
    glyf = font["glyf"]
    order = list(font.getGlyphOrder())

    import_interrobang(font, weight)
    # import 直接写了 glyf.glyphs 但可能未更新 glyphOrder；
    # 以「实际 glyphs 键」为准重建（不能再用返回名拼接——可能重复）
    glyph_keys = list(glyf.glyphs.keys())
    font.setGlyphOrder(glyph_keys)
    glyf.glyphOrder = glyph_keys
    order = glyph_keys
    # 2) Th 连字：从 Hanken 源 VF 的对应字重提取 T_h。
    th_vf = HANKEN_VF / (f"HankenGrotesk-Italic-VariableFont_wght.ttf" if ITALIC else f"HankenGrotesk-VariableFont_wght.ttf")
    if th_vf.exists() and "T_h" not in order:
        hanken_variable = TTFont(th_vf)
        hf = instantiateVariableFont(
            hanken_variable, {"wght": weight},
            inplace=False, optimize=True, static=True,
        )
        hanken_variable.close()
        if "T_h" in hf.getGlyphOrder():
            import_hanken_ligature(font, hf, "T_h")
            # glyf.__setitem__ 在部分 fontTools 版本会自动把新名字追加进
            # glyphOrder；这里防御式去重，避免双重 append 导致 save 断言失败
            if "T_h" not in order:
                order.append("T_h")
        hf.close()
    font.setGlyphOrder(order)
    glyf.glyphOrder = order

    # 3) liga：?! -> ‽、？！-> 全宽‽、T+h -> T_h 全部默认开启
    gsub = font["GSUB"].table
    # 半角 ?/! 会被 locl 切到隐藏字形（如 en 下的 Hanken hidden），
    # 收集所有变体字形，让连字在任何本地化状态下都能匹配。
    def locl_variants(glyph):
        out = {glyph}
        for sr in gsub.ScriptList.ScriptRecord:
            for lr in sr.Script.LangSysRecord:
                for fi in lr.LangSys.FeatureIndex:
                    fr = gsub.FeatureList.FeatureRecord[fi]
                    if fr.FeatureTag != "locl":
                        continue
                    for li in fr.Feature.LookupListIndex:
                        lk = gsub.LookupList.Lookup[li]
                        for st in lk.SubTable:
                            typ = lk.LookupType
                            if typ == 7:
                                typ = st.ExtensionLookupType
                                st = st.ExtSubTable
                            if typ == 1 and hasattr(st, "mapping") and glyph in st.mapping:
                                out.add(st.mapping[glyph])
        return out

    q_variants = locl_variants("question")
    e_variants = locl_variants("exclam")
    liga_mapping = {}
    for q in q_variants:
        for e in e_variants:
            if q in font.getGlyphOrder() and e in font.getGlyphOrder():
                # 双向：?! 和 !? 都连成 ‽
                liga_mapping[(q, e)] = "interrobang.uni203D"
                liga_mapping[(e, q)] = "interrobang.uni203D"
    liga_mapping[("uniFF1F", "uniFF01")] = "interrobang.full"
    liga_mapping[("uniFF01", "uniFF1F")] = "interrobang.full"
    if "T_h" in order:
        liga_mapping[("T", "h")] = "T_h"
    st = buildLigatureSubstSubtable(liga_mapping)
    lk = buildLookup([st], table="GSUB")
    gsub.LookupList.Lookup.append(lk)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    new_li = len(gsub.LookupList.Lookup) - 1
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "liga":
            # 插到最前：让连字在 locl/ccmp 之前执行，否则半角 ?! 会被
            # 本地化切走导致匹配失败
            fr.Feature.LookupListIndex.insert(0, new_li)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)

    set_names(font, weight, style)
    try:
        buildStatTable(font, [dict(tag="wght", name="Weight",
                                   values=[dict(value=weight, name=style, flags=0x2 if weight == 400 else 0)])])
    except Exception:
        pass

    out = OUT / (f"{PS}-Italic.ttf" if (ITALIC and weight == 400) else f"{PS}-{style}{'Italic' if ITALIC else ''}.ttf")
    font.save(out, reorderTables=True)
    font.close()
    print(f"done {style}{' Italic' if ITALIC else ''} {out.stat().st_size/1048576:.2f} MiB", flush=True)
    return out


if __name__ == "__main__":
    validate_inter_source()
    only = os.environ.get("HANLINK_ONLY_WEIGHT")
    selected = WEIGHTS if not only else {int(only): WEIGHTS[int(only)]}
    for w, s in selected.items():
        build_weight(w, s)
    print("Hanlink ?! static build complete")
