# Building Hanlink Sans

Hanlink Sans is built from three OFL-licensed upstream font families. Noto Sans SC and Hanken Grotesk are taken exclusively from pinned **Google Fonts repository distributions**, never author-repository, system, or mirror builds. Exact revisions and hashes are recorded in `SOURCES.md`.

## 1. Fetch Google Fonts inputs

```bash
python scripts/fetch_sources.py
```

This downloads the pinned Google Fonts variable TTFs into gitignored `sources/`, verifies SHA-256, and generates all nine static source instances locally.

Build CJK Punct Bridge v1.2.0 in a sibling `CJK-Punct-Bridge` directory, or set `HANLINK_BRIDGE_DIR` to that checkout.

## 2. Build and verify

```bash
python scripts/build_static_reference.py
python scripts/build_variable_reference.py
python scripts/audit_release.py fonts/static/*.ttf fonts/variable/*.ttf
python scripts/check_dash_matrix.py fonts/static/*.ttf fonts/variable/*.ttf
python scripts/render_regression.py
```

The italic family is a separate build pass: set `HANLINK_ITALIC=1` for
`build_static_reference.py` and `build_variable_reference.py` to emit the nine
`fonts/static/HanlinkSans-*Italic.ttf` faces and
`fonts/variable/HanlinkSans-Italic-Variable.ttf`. The CJK Punct Bridge sibling
checkout must have been built with `CJK_PUNCT_ITALIC=1` first so its italic
static faces exist. Regression scripts accept `HANLINK_ITALIC_TEST=1` to
compare the italic Latin against the Hanken Grotesk Italic source.

## Inputs

- Hanken Grotesk: Latin, ordinary Western digits and most Western symbols.
- Noto Sans SC: Han/CJK coverage, default CJK punctuation, metrics and vertical layout data.
- Zhudou Sans: CJK em-dash outlines, including continuous two-em/three-em and vertical dash forms.

Hanlink Sans uses the same audited punctuation layer as CJK Punct Bridge. That layer resolves Noto's Simplified-Chinese `locl` dash targets and their true `vert` targets from GSUB, rather than assuming glyph names.

## Static family

Nine static TTF faces are produced at weights 100–900.

The italic family mirrors that pipeline with `HANLINK_ITALIC=1`: Hanken
Grotesk Italic supplies the true italic Latin designs, while Noto Sans SC and
the CJK Punct Bridge italic sources get a uniform synthetic 10-degree shear
(`shear_font()` in `build_static_reference.py`) because no true CJK italic
design exists. Simple glyphs keep their exact point structure and flags so
varLib masters stay interpolatable; composites are decomposed identically on
every master; advance widths stay unchanged and left side bearings are
recomputed from the new bounds.

For each weight:

1. Build or load the matching fixed CJK punctuation bridge layer.
2. Reserve punctuation code points covered by that bridge.
3. Take remaining Latin/Western coverage from Hanken Grotesk.
4. Take remaining CJK coverage from Noto Sans SC.
5. Preserve Noto Sans SC horizontal/vertical metrics and CJK OpenType layout behavior.
6. Normalize family/style naming to `Hanlink Sans` and set Office-compatible legacy style linking.

The static Google Fonts Noto instances and CJK Punct Bridge can retain a source-specific `BASE` ItemVariationStore. `fontTools.merge` cannot combine those stores, so Hanlink removes `BASE` from merge inputs and explicitly normalizes final horizontal/vertical metrics to Noto Sans SC. `GSUB`, `GPOS`, `vhea`, and `vmtx` remain audited and preserved.

## Variable font

The variable build uses all nine audited static faces as designspace masters and lets fontTools varLib generate `gvar`/metric variation data. This avoids unsafe manual GID-based tuple grafting. It preserves a `wght` axis from 100 to 900 with 400 as the default; Regular's audited CJK layout tables remain the stable layout layer.

The italic variable font is built the same way from the nine italic static
faces (`HANLINK_ITALIC=1`), producing `HanlinkSans-Italic-Variable.ttf` with a
`wght` axis from 100 to 900. Upright and italic are separate single-axis
variable files sharing the typographic family name **Hanlink Sans**, exactly
like the pinned Hanken Grotesk release (`HankenGrotesk[wght].ttf` +
`HankenGrotesk-Italic[wght].ttf`).

## OpenType behavior

- Default/no-language punctuation is CJK-oriented and remains Noto SC-based.
- Default `U+2014` uses the Zhudou-derived CJK form.
- Repeated `U+2014` uses `ccmp` to form continuous two-em/three-em dashes in default/CJK language systems.
- Every configured explicit Western language under Common, Latin, Cyrillic, or Greek runs receives `locl` alternates for all 46 punctuation code points shared by CJK Punct Bridge and Hanken Grotesk. Common-script coverage keeps English `1/2` and similar punctuation/number runs from falling through to the no-language default.
- ASCII `U+0030`–`U+0039` are always Hanken-owned. Audits require exact source outlines and metrics and reject any default, Western, or CJK `locl` path that substitutes those ten public glyphs.
- Explicit Western-language paths omit the CJK continuous-dash substitution, so repeated em dashes remain separate Hanken glyphs. Script defaults and explicit CJK language systems retain their Noto regional behavior.
- `vert`, `vrt2`, `vhea`, and `vmtx` are retained for CJK vertical layout.
- Regression scripts verify the complete 46-code-point Hanken provenance, every explicit Western language system, CJK regional aliases, horizontal/vertical Chinese dashes, and the Western no-ligation policy.

## Distribution

Prebuilt TTF files are published as GitHub Release assets and are intentionally omitted from normal Git history.
