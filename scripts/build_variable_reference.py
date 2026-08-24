from copy import deepcopy
from pathlib import Path
import os

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from font_metadata import apply_binary_metadata, project_names

REPO = Path(__file__).resolve().parents[1]
STATIC = REPO / "fonts/static"
OUT = REPO / "fonts/variable"
WORK = Path(os.environ.get("HANLINK_VF_BUILD_DIR", REPO / "build/vf"))
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

FAMILY = "Hanlink Sans"
PS = "HanlinkSans"
ITALIC = os.environ.get("HANLINK_ITALIC") == "1"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
def setname(table, name_id, value):
    table.names = [record for record in table.names if record.nameID != name_id]
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
        **project_names(unique), 1: FAMILY, 2: sub, 4: FAMILY + (f" {sub}" if ITALIC else ""),
        6: f"{PS}{'-Italic' if ITALIC else ''}", 16: FAMILY, 17: sub, 25: PS,
    }
    for name_id, value in values.items():
        setname(names, name_id, value)
    apply_binary_metadata(font)
    os2 = font["OS/2"]
    os2.usWeightClass = 400
    for bit in (0, 5, 6, 9):
        os2.fsSelection &= ~(1 << bit)
    os2.fsSelection |= 1 << 6
    if ITALIC:
        os2.fsSelection |= 1 << 0
    font["head"].macStyle &= ~3
    if ITALIC:
        font["head"].macStyle |= 2


paths = {weight: STATIC / (f"{PS}-Italic.ttf" if (ITALIC and weight == 400) else f"{PS}-{style}{'Italic' if ITALIC else ''}.ttf") for weight, style in WEIGHTS.items()}
missing = [str(path) for path in paths.values() if not path.exists()]
if missing:
    raise SystemExit("Missing static masters:\n" + "\n".join(missing))

orders = []
for path in paths.values():
    font = TTFont(path, lazy=True)
    orders.append(font.getGlyphOrder())
    font.close()
if not all(order == orders[0] for order in orders[1:]):
    raise SystemExit("Static master glyph orders differ")

def style_names():
    return [
        ("Italic" if (ITALIC and weight == 400) else style + (" Italic" if ITALIC else ""))
        for weight, style in WEIGHTS.items()
    ]

designspace = DesignSpaceDocument()
axis = AxisDescriptor()
axis.name = "Weight"
axis.tag = "wght"
axis.minimum = 100
axis.default = 400
axis.maximum = 900
designspace.addAxis(axis)

for (weight, style), style_name in zip(WEIGHTS.items(), style_names()):
    source = SourceDescriptor()
    source.path = str(paths[weight])
    source.name = f"master.{weight}"
    source.familyName = FAMILY
    source.styleName = style_name
    source.location = {"Weight": weight}
    if weight == 400:
        source.copyInfo = True
        source.copyLib = True
        source.copyGroups = True
        source.copyFeatures = True
    designspace.addSource(source)

    instance = InstanceDescriptor()
    instance.name = style_name
    instance.familyName = FAMILY
    instance.styleName = style_name
    instance.location = {"Weight": weight}
    designspace.addInstance(instance)

designspace_path = WORK / f"{PS}.designspace"
designspace.write(designspace_path)
print("build variable from", len(paths), "audited static masters", flush=True)
variable, _, _ = varlib_build(
    str(designspace_path), exclude=["BASE", "GDEF", "GPOS", "GSUB"]
)

regular = TTFont(paths[400])
for tag in ("GDEF", "GPOS", "GSUB", "prep"):
    if tag in regular:
        variable[tag] = deepcopy(regular[tag])
regular.close()

set_names(variable)
names = variable["name"]
for instance, style_name in zip(variable["fvar"].instances, style_names()):
    instance.subfamilyNameID = names.addName(
        style_name, platforms=((3, 1, 0x409), (1, 0, 0))
    )
stat_values = [dict(
    tag="wght", name="Weight",
    values=[
        dict(value=weight, name=style_name, flags=0x2 if weight == 400 else 0)
        for (weight, style), style_name in zip(WEIGHTS.items(), style_names())
    ],
)]
if ITALIC:
    stat_values.append(dict(tag="ital", name="Italic", values=[dict(value=1, name="Italic")]))
try:
    buildStatTable(variable, stat_values)
except Exception as error:
    print("STAT warning", error, flush=True)

output = OUT / f"{PS}{'-Italic' if ITALIC else ''}-Variable.ttf"
variable.save(output, reorderTables=True)
variable.close()
print("saved", output, output.stat().st_size / 1048576, "MiB", flush=True)

variable = TTFont(output)
axis = next(item for item in variable["fvar"].axes if item.axisTag == "wght")
assert (axis.minValue, axis.defaultValue, axis.maxValue) == (100.0, 400.0, 900.0)
assert len(variable["fvar"].instances) == 9
for weight, style in ((100, "Thin"), (400, "Regular"), (900, "Black")):
    instance = instantiateVariableFont(
        variable, {"wght": weight}, inplace=False, optimize=True, static=True
    )
    static = TTFont(paths[weight])
    instance_cmap = instance.getBestCmap()
    static_cmap = static.getBestCmap()
    for cp in (0x0041, 0x0061, 0x002F, 0x2014, 0x4E2D, 0xFF0C):
        assert instance["hmtx"].metrics[instance_cmap[cp]] == static["hmtx"].metrics[static_cmap[cp]], (
            weight, hex(cp), "advance mismatch"
        )
    instance.close()
    static.close()
variable.close()
print("validated variable endpoints/default", flush=True)
