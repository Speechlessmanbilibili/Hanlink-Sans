#!/usr/bin/env python3
"""RAQM rendering regression checks for Hanlink Sans.

Requires Pillow built with libraqm. The checks compare Hanlink's public shaping
against the corresponding upstream source for representative Latin and CJK
cases. Structural script remaps (Greek/Bopomofo shared glyphs) are covered by
``audit_release.py`` because subpixel positioning can differ slightly after
font merging even when glyph outlines and metrics are identical.
"""
from pathlib import Path
import os
from PIL import ImageFont, features

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("HANLINK_BUILD_WORKSPACE", ROOT.parent))
UPSTREAM = Path(os.environ.get("HANLINK_UPSTREAM_DIR", WORKSPACE / "wordfont_build"))
HANLINK = ROOT / "fonts/static/HanlinkSans-Regular.ttf"
HANKEN = UPSTREAM / "hanken/static/HankenGrotesk-Regular.ttf"
NOTO = UPSTREAM / "noto/static/NotoSansSC-Regular.ttf"

if not features.check_feature("raqm"):
    raise SystemExit("Pillow was built without libraqm")

def load(path):
    return ImageFont.truetype(str(path), 120, layout_engine=ImageFont.Layout.RAQM)

def mask(font, text, language, features_=()):
    m = font.getmask(text, direction="ltr", language=language, features=list(features_))
    return m.size, bytes(m)

def length(font, text, language, features_=()):
    return font.getlength(text, direction="ltr", language=language, features=list(features_))

hl, hk, no = map(load, (HANLINK, HANKEN, NOTO))

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
    assert mask(hl, text, lang, feats) == mask(hk, text, lang, feats), (
        "Hanken render mismatch", text, lang, feats
    )

noto_cases = [
    ("中文，。", "zh-CN", ()),
    ("Русский", "ru", ()),
    ("かな、。", "ja", ()),
    ("ㄓˇ", "zh-Bopo", ()),
]
for text, lang, feats in noto_cases:
    assert mask(hl, text, lang, feats) == mask(no, text, lang, feats), (
        "Noto render mismatch", text, lang, feats
    )

for text, lang in (("ΑΩμ", "el"), ("ㄓˇㄨˋ", "zh-Bopo")):
    assert abs(length(hl, text, lang) - length(no, text, lang)) < 0.01, (
        "Noto metric mismatch", text, lang
    )

assert abs(length(hl, "——", "en") - length(hk, "——", "en")) < 0.01
assert abs(length(hl, "———", "en") - length(hk, "———", "en")) < 0.01

print("PASS: RAQM upstream rendering regression")
