#!/usr/bin/env python3
"""Hanlink ?! 可变字体构建：从 fonts-interrobang/static 的 9 个静态 master 构建。

用法：
    python scripts/build_variable_interrobang.py              # 正体 VF
    HANLINK_ITALIC=1 python scripts/build_variable_interrobang.py  # 斜体 VF
"""
from copy import deepcopy
from pathlib import Path
import os
from fontTools.designspaceLib import (
    AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from font_metadata import apply_binary_metadata, project_names
from build_interrobang import INTER_LEGAL

REPO = Path(__file__).resolve().parents[1]
STATIC = REPO / "fonts-interrobang" / "static"
OUT = REPO / "fonts-interrobang" / "variable"
WORK = REPO / "build" / "interrobang-vf"
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

FAMILY = "Hanlink ?!"
PS = "HanlinkSansInterrobang"
ITALIC = os.environ.get("HANLINK_ITALIC") == "1"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
MAX_GLYPHS = 60_000
MAX_GVAR_BYTES = 64 * 1024 * 1024


def setname(table, name_id, value):
    table.names = [r for r in table.names if r.nameID != name_id]
    table.setName(value, name_id, 3, 1, 0x409)
    try:
        value.encode("mac_roman")
        table.setName(value, name_id, 1, 0, 0)
    except Exception:
        pass


def set_names(font):
    names = font["name"]
    sub = "Italic" if ITALIC else "Regular"
    unique = f"{PS}-Italic-VF" if ITALIC else f"{PS}-VF"
    values = {
        **project_names(unique),
        **INTER_LEGAL,
        1: FAMILY, 2: sub, 4: FAMILY + (f" {sub}" if ITALIC else ""),
        6: f"{PS}{'-Italic' if ITALIC else ''}", 16: FAMILY, 17: sub, 25: PS,
    }
    for nid, val in values.items():
        setname(names, nid, val)
    apply_binary_metadata(font)
    os2 = font["OS/2"]
    os2.usWeightClass = 400
    for bit in (0, 5, 6, 9):
        os2.fsSelection &= ~(1 << bit)
    if not ITALIC:
        os2.fsSelection |= 1 << 6
    if ITALIC:
        os2.fsSelection |= 1 << 0
    font["head"].macStyle &= ~3
    if ITALIC:
        font["head"].macStyle |= 2


def style_names():
    return [
        ("Italic" if (ITALIC and weight == 400) else style + (" Italic" if ITALIC else ""))
        for weight, style in WEIGHTS.items()
    ]


def glyph_signature(font, glyph_name):
    glyph = font["glyf"][glyph_name]
    coords, end_points, flags = glyph.getCoordinates(font["glyf"])
    return (
        tuple(coords), tuple(end_points), bytes(flags),
        font["hmtx"].metrics[glyph_name],
    )


def interrobang_targets(font):
    cmap = font.getBestCmap()
    pairs = ((cmap[0x003F], cmap[0x0021]), (cmap[0xFF1F], cmap[0xFF01]))
    targets = []
    for first, second in pairs:
        target = None
        for lookup in reversed(font["GSUB"].table.LookupList.Lookup):
            for subtable in lookup.SubTable:
                lookup_type = lookup.LookupType
                if lookup_type == 7:
                    lookup_type = subtable.ExtensionLookupType
                    subtable = subtable.ExtSubTable
                if lookup_type != 4 or not hasattr(subtable, "ligatures"):
                    continue
                for ligature in subtable.ligatures.get(first, []):
                    if ligature.Component == [second]:
                        target = ligature.LigGlyph
                        break
                if target is not None:
                    break
            if target is not None:
                break
        if target is None:
            raise AssertionError((first, second, "missing interrobang ligature"))
        targets.append(target)
    return tuple(targets)


def validate_output(output, paths):
    variable = TTFont(output)
    axis = next(item for item in variable["fvar"].axes if item.axisTag == "wght")
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (100.0, 400.0, 900.0)
    assert len(variable["fvar"].instances) == 9
    glyph_count = variable["maxp"].numGlyphs
    gvar_bytes = variable.reader.tables["gvar"].length
    assert glyph_count < MAX_GLYPHS, ("Office/GDI glyph guard", glyph_count, MAX_GLYPHS)
    assert gvar_bytes < MAX_GVAR_BYTES, ("Office/GDI gvar guard", gvar_bytes, MAX_GVAR_BYTES)

    outline_signatures = []
    for weight in WEIGHTS:
        static = TTFont(paths[weight])
        half_static, full_static = interrobang_targets(static)
        outline_signatures.append(glyph_signature(static, half_static))
        if weight in (100, 400, 900):
            instance = instantiateVariableFont(
                variable, {"wght": weight}, inplace=False, optimize=True, static=True
            )
            half_instance, full_instance = interrobang_targets(instance)
            for variable_name, static_name in (
                (half_instance, half_static), (full_instance, full_static),
            ):
                assert glyph_signature(instance, variable_name) == glyph_signature(static, static_name), (
                    weight, variable_name, "variable/static interrobang mismatch"
                )
            instance.close()
        static.close()
    assert len(set(outline_signatures)) == len(WEIGHTS), "Inter U+203D outline does not vary by weight"
    variable.close()
    print(
        f"validated 9 distinct interrobang weights; glyphs={glyph_count}; "
        f"gvar={gvar_bytes} bytes",
        flush=True,
    )


def main():
    paths = {
        weight: STATIC / (f"{PS}-Italic.ttf" if (ITALIC and weight == 400) else f"{PS}-{style}{'Italic' if ITALIC else ''}.ttf")
        for weight, style in WEIGHTS.items()
    }
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise SystemExit("Missing static masters:\n" + "\n".join(missing))

    orders = []
    for path in paths.values():
        font = TTFont(path, lazy=True)
        orders.append(font.getGlyphOrder())
        font.close()
    if not all(o == orders[0] for o in orders[1:]):
        raise SystemExit("Static master glyph orders differ")

    ds = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name = "Weight"
    axis.tag = "wght"
    axis.minimum = 100
    axis.default = 400
    axis.maximum = 900
    ds.addAxis(axis)
    for (weight, style), style_name in zip(WEIGHTS.items(), style_names()):
        src = SourceDescriptor()
        src.path = str(paths[weight])
        src.name = f"master.{weight}"
        src.familyName = FAMILY
        src.styleName = style_name
        src.location = {"Weight": weight}
        if weight == 400:
            src.copyInfo = True
            src.copyLib = True
            src.copyGroups = True
            src.copyFeatures = True
        ds.addSource(src)
        ins = InstanceDescriptor()
        ins.name = style_name
        ins.familyName = FAMILY
        ins.styleName = style_name
        ins.location = {"Weight": weight}
        ds.addInstance(ins)
    dsp = WORK / f"{PS}{'-Italic' if ITALIC else ''}.designspace"
    ds.write(dsp)

    variable, _, _ = varlib_build(str(dsp), exclude=["BASE", "GDEF", "GPOS", "GSUB"])
    reg = TTFont(paths[400])
    for tag in ("GDEF", "GPOS", "GSUB", "prep"):
        if tag in reg:
            table = deepcopy(reg[tag])
            if hasattr(table, "VarStore") and table.VarStore is not None:
                table.VarStore = None
            variable[tag] = table
    reg.close()

    set_names(variable)
    names = variable["name"]
    for inst, style_name in zip(variable["fvar"].instances, style_names()):
        inst.subfamilyNameID = names.addName(style_name, platforms=((3, 1, 0x409), (1, 0, 0)))
    stat_values = [dict(tag="wght", name="Weight", values=[
        dict(value=w, name=n, flags=0x2 if w == 400 else 0)
        for (w, s), n in zip(WEIGHTS.items(), style_names())
    ])]
    if ITALIC:
        stat_values.append(dict(tag="ital", name="Italic", values=[dict(value=1, name="Italic")]))
    try:
        buildStatTable(variable, stat_values)
    except Exception as e:
        print("STAT warning", e, flush=True)

    output = OUT / f"{PS}{'-Italic' if ITALIC else ''}-Variable.ttf"
    variable.save(output, reorderTables=True)
    variable.close()
    print("saved", output, output.stat().st_size / 1048576, "MiB", flush=True)
    validate_output(output, paths)


if __name__ == "__main__":
    main()
