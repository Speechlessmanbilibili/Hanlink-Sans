#!/usr/bin/env python3
"""HarfBuzz shaping and RAQM rendering regressions for Hanlink Sans.

Requires Pillow built with libraqm. The checks compare Hanlink's public shaping
against the corresponding upstream source for representative Latin and CJK
cases. Structural script remaps (Greek/Bopomofo shared glyphs) are covered by
``audit_release.py`` because subpixel positioning can differ slightly after
font merging even when glyph outlines and metrics are identical.
"""
from pathlib import Path
import os
from PIL import Image, ImageFont, features
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("HANLINK_BUILD_WORKSPACE", ROOT.parent))
UPSTREAM = Path(os.environ.get("HANLINK_UPSTREAM_DIR", ROOT / "sources"))
HANLINK = Path(os.environ.get("HANLINK_TEST_FONT", ROOT / "fonts/static/HanlinkSans-Regular.ttf"))
HANKEN = UPSTREAM / "hanken/static/HankenGrotesk-Regular.ttf"
NOTO = UPSTREAM / "noto/static/NotoSansSC-Regular.ttf"

if not features.check_feature("raqm"):
    raise SystemExit("Pillow was built without libraqm")

def load(path):
    return ImageFont.truetype(str(path), 120, layout_engine=ImageFont.Layout.RAQM)

def visible_width(font, text, language, features_=()):
    m = font.getmask(text, direction="ltr", language=language, features=list(features_))
    image = Image.frombytes("L", m.size, bytes(m))
    box = image.getbbox()
    return 0 if box is None else box[2] - box[0]

def shape(path, text, language, features_=()):
    face = hb.Face(path.read_bytes())
    font = hb.Font(face)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    if language is not None:
        buffer.language = language
    hb.shape(font, buffer, {tag: True for tag in features_})
    return tuple(
        (info.cluster, pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset)
        for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)
    )

hl = load(HANLINK)

hanken_cases = [
    ("office", "en", ()),
    ("efficient", "en", ()),
    ("l·l", "ca", ()),
    ("IJ", "nl", ()),
    ("i", "tr", ()),
    ("Ō", "mh", ()),
    ("1/2", "en", ("frac",)),
    ("3rd", "en", ("ordn",)),
    ("a", "en", ("ss01",)),
    ("g", "en", ("ss02",)),
    ("G", "en", ("ss03",)),
]
for text, lang, feats in hanken_cases:
    assert visible_width(hl, text, lang, feats) > 0
    assert shape(HANLINK, text, lang, feats) == shape(HANKEN, text, lang, feats), (
        "Hanken shaping/metric mismatch", text, lang, feats
    )

# Digits are an invariant Hanken-owned run. Language metadata may change
# punctuation, but must not change the outlines or advances selected for 0-9.
for lang in (None, "en", "de", "fr", "ru", "uk", "el", "zh-CN", "zh-TW", "ja", "ko"):
    assert shape(HANLINK, "0123456789", lang) == shape(HANKEN, "0123456789", lang), (
        "Hanken digit shaping/metric mismatch", lang
    )

noto_cases = [
    ("中文，。", "zh-CN", ()),
    ("Русский", "ru", ()),
    ("かな、。", "ja", ()),
    ("ㄓˇ", "zh-Bopo", ()),
]
for text, lang, feats in noto_cases:
    assert visible_width(hl, text, lang, feats) > 0
    assert shape(HANLINK, text, lang, feats) == shape(NOTO, text, lang, feats), (
        "Noto shaping/metric mismatch", text, lang, feats
    )

for text, lang in (("ΑΩμ", "el"), ("ㄓˇㄨˋ", "zh-Bopo")):
    assert shape(HANLINK, text, lang) == shape(NOTO, text, lang), ("Noto metric mismatch", text, lang)

assert shape(HANLINK, "——", "en") == shape(HANKEN, "——", "en")
assert shape(HANLINK, "———", "en") == shape(HANKEN, "———", "en")

print("PASS: HarfBuzz shaping and RAQM rendering regression")
