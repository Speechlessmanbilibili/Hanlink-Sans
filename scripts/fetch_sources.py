from pathlib import Path
import hashlib
import urllib.request
import zipfile

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
NOTO_CJK_ZIP = (
    "https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/"
    "02_NotoSansCJK-TTF-VF.zip",
    "b73a1f90988d6ccc3f60ce44ee3d1e82479a92710cd49cd950950c9adab50f1e",
)
INPUTS = {
    "hanken/HankenGrotesk-VariableFont_wght.ttf": (
        "https://raw.githubusercontent.com/google/fonts/714891563e901b1a0d8ebcaaa003b01604793888/"
        "ofl/hankengrotesk/HankenGrotesk%5Bwght%5D.ttf",
        "813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f",
        "HankenGrotesk", False,
    ),
    "hanken/HankenGrotesk-Italic-VariableFont_wght.ttf": (
        "https://raw.githubusercontent.com/google/fonts/714891563e901b1a0d8ebcaaa003b01604793888/"
        "ofl/hankengrotesk/HankenGrotesk-Italic%5Bwght%5D.ttf",
        "ae5731726ff75301a3cb63f2e98d1babc77d55ab09fb8e229ca75f5bd46fbe32",
        "HankenGrotesk", True,
    ),
    "noto/NotoSansSC-VariableFont_wght.ttf": (
        "https://raw.githubusercontent.com/google/fonts/2894aab31764f10f29c421bdfd2340d3b382d384/"
        "ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
        "a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da",
        "NotoSansSC", False,
    ),
}

for relative, (url, expected, family, italic) in INPUTS.items():
    path = SOURCES / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print("download", relative, flush=True)
        urllib.request.urlretrieve(url, path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"{relative}: SHA-256 mismatch: {actual}")
    print("ok", relative, actual)

    static_dir = path.parent / "static"
    static_dir.mkdir(exist_ok=True)
    variable = TTFont(path)
    for weight, style in WEIGHTS.items():
        if italic:
            output = static_dir / f"{family}-Italic-{style}.ttf"
        else:
            output = static_dir / f"{family}-{style}.ttf"
        instance = instantiateVariableFont(
            variable, {"wght": weight}, inplace=False, optimize=True, static=True
        )
        instance.save(output, reorderTables=True)
        instance.close()
    variable.close()

# Noto CJK 四地合一 TTF-VF（区域字形变体源）：Sans2.004 官方发布。
zip_path = SOURCES / "noto-cjk" / "NotoSansCJK-TTF-VF.zip"
zip_path.parent.mkdir(parents=True, exist_ok=True)
if not zip_path.exists():
    print("download NotoSansCJK-TTF-VF.zip", flush=True)
    urllib.request.urlretrieve(NOTO_CJK_ZIP[0], zip_path)
actual = hashlib.sha256(zip_path.read_bytes()).hexdigest()
if actual != NOTO_CJK_ZIP[1]:
    raise SystemExit(f"NotoSansCJK-TTF-VF.zip: SHA-256 mismatch: {actual}")
print("ok NotoSansCJK-TTF-VF.zip", actual)

cjk_vf = SOURCES / "noto-cjk" / "Variable" / "TTF" / "NotoSansCJKsc-VF.ttf"
if not cjk_vf.exists():
    with zipfile.ZipFile(zip_path) as z:
        z.extract("Variable/TTF/NotoSansCJKsc-VF.ttf", zip_path.parent)
cjk_static = SOURCES / "noto-cjk" / "static"
cjk_static.mkdir(exist_ok=True)
if not list(cjk_static.glob("*.ttf")):
    variable = TTFont(cjk_vf)
    for weight, style in WEIGHTS.items():
        output = cjk_static / f"NotoSansSC-{style}.ttf"
        instance = instantiateVariableFont(
            variable, {"wght": weight}, inplace=False, optimize=True, static=True
        )
        instance.save(output, reorderTables=True)
        instance.close()
    variable.close()
print("Noto CJK sources ready:", cjk_static)

print("Google Fonts sources ready:", SOURCES)
