#!/usr/bin/env python3
"""Th Grotesk —— Hanken Grotesk 的 Th 连字变体。

把 Hanken 的可选连字 T+h -> T_h（dlig）搬到默认开启的 liga，
其余字形/特性/字重全部保持 Hanken 原样。家族名 Th Grotesk。

输出：
  fonts/ThGrotesk-Variable.ttf（wght 100-900）
  fonts/static/ThGrotesk-{Weight}.ttf（选 --static 时生成）
"""
from copy import deepcopy
from pathlib import Path
import os
import sys
import argparse
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

REPO = Path(__file__).resolve().parents[1]
ITALIC = os.environ.get("HANKEN_ITALIC") == "1"
SRC = Path(os.environ.get(
    "HANKEN_VF",
    REPO.parent / "hanlink-sans" / "sources" / "hanken" /
    (f"HankenGrotesk-Italic-VariableFont_wght.ttf" if ITALIC else f"HankenGrotesk-VariableFont_wght.ttf"),
))
OUT = REPO / "fonts"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
FAMILY = "Th Grotesk"
PS = "ThGrotesk"


def poster_suffix():
    return "Italic" if ITALIC else ""


def setname(font, nid, val):
    nt = font["name"]
    nt.names = [r for r in nt.names if r.nameID != nid]
    nt.setName(val, nid, 3, 1, 0x409)
    try:
        val.encode("mac_roman")
        nt.setName(val, nid, 1, 0, 0)
    except Exception:
        pass


def rename_family(font):
    """家族名统一改为 Th Grotesk；斜体时子家族带 Italic。"""
    nt = font["name"]
    sub = poster_suffix()
    # 先取原值，再统一 setname（避免循环内重复 set）
    def get(nid):
        rec = nt.getName(nid, 3, 1, 0x409)
        return rec.toUnicode() if rec else None
    for nid in (1, 16):
        prev = get(nid)
        if prev:
            setname(font, nid, FAMILY)
    # full/typo 名：Th Grotesk [style]（斜体追加 Italic）
    for nid in (4, 21):
        prev = get(nid)
        if not prev:
            continue
        style_part = prev
        for fam in ("Hanken Grotesk", FAMILY):
            if style_part.startswith(fam):
                style_part = style_part[len(fam):].strip()
                break
        style_part = style_part.replace(" Italic", "").strip()
        new_val = FAMILY + (f" {style_part}" if style_part else "")
        if sub and not new_val.endswith("Italic"):
            new_val += f" {sub}" if style_part else f" {sub}"
        setname(font, nid, new_val)
    if sub:
        for nid in (2, 17):
            prev = get(nid)
            if prev and not prev.endswith("Italic"):
                setname(font, nid, f"{prev} Italic")


def move_th_to_liga(font):
    """把 dlig 的 ligature lookup 引用加到 liga（T+h -> T_h 默认开启）。"""
    gsub = font["GSUB"].table
    dlig_lookups = []
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "dlig":
            dlig_lookups.extend(fr.Feature.LookupListIndex)
    added = 0
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "liga":
            for li in dlig_lookups:
                if li not in fr.Feature.LookupListIndex:
                    fr.Feature.LookupListIndex.append(li)
                    added += 1
            fr.Feature.LookupListIndex.sort()
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
    return added


def build_variable():
    vf = TTFont(SRC)
    moved = move_th_to_liga(vf)
    # 家族/子家族名
    rename_family(vf)
    # 斜体样式位
    if ITALIC:
        vf["OS/2"].fsSelection |= 1 << 0
        vf["head"].macStyle |= 2
    vf["head"].fontRevision = 1.0
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{PS}{'-Italic' if ITALIC else ''}-Variable.ttf"
    vf.save(out, reorderTables=True)
    vf.close()
    print(f"moved {moved} dlig lookups to liga; saved {out}")


def build_statics():
    statics = OUT / "static"
    statics.mkdir(parents=True, exist_ok=True)
    for weight, style in WEIGHTS.items():
        font = instantiateVariableFont(TTFont(SRC), {"wght": weight}, inplace=False, optimize=True, static=True)
        moved = move_th_to_liga(font)
        # instancer 可能裁掉 T_h 字形（隐藏字形）；从源 VF 补拷
        src_vf = TTFont(SRC)
        for name in ("T_h",):
            if name not in font.getGlyphOrder() and name in src_vf["glyf"]:
                font["glyf"][name] = deepcopy(src_vf["glyf"][name])
                font["hmtx"].metrics[name] = src_vf["hmtx"].metrics[name]
                order = list(font.getGlyphOrder())
                order.append(name)
                font.setGlyphOrder(order)
        src_vf.close()
        rename_family(font)
        if ITALIC:
            font["OS/2"].fsSelection |= 1 << 0
            font["head"].macStyle |= 2
        font["head"].fontRevision = 1.0
        if ITALIC:
            fname = f"{PS}-Italic.ttf" if weight == 400 else f"{PS}-{style}Italic.ttf"
        else:
            fname = f"{PS}-{style}.ttf"
        out = statics / fname
        font.save(out, reorderTables=True)
        font.close()
        print(f"  {style}: moved {moved} lookups, saved {out.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true", help="同时生成 9 个静态权重")
    args = ap.parse_args()
    build_variable()
    if args.static:
        build_statics()
