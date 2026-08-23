# Building Hanlink Sans

Hanlink Sans is built from three OFL-licensed upstream font families. Exact source archive hashes are recorded in `SOURCES.md`.

## Inputs

- Hanken Grotesk: Latin, ordinary Western digits and most Western symbols.
- Noto Sans SC: Han/CJK coverage, default CJK punctuation, metrics and vertical layout data.
- Zhudou Sans: CJK em-dash outlines, including continuous two-em/three-em and vertical dash forms.

## Static family

Nine static TTF faces are produced at weights 100–900.

For each weight:

1. Build or load the matching CJK punctuation bridge layer.
2. Reserve punctuation code points covered by that bridge.
3. Take remaining Latin/Western coverage from Hanken Grotesk.
4. Take remaining CJK coverage from Noto Sans SC.
5. Preserve Noto Sans SC horizontal/vertical metrics and CJK OpenType layout behavior.
6. Normalize family/style naming to `Hanlink Sans` and set Office-compatible legacy style linking.

## Variable font

The variable build uses the same Unicode split and family naming, preserving a `wght` axis from 100 to 900 with 400 as the default. The Regular CJK layout tables are retained as the stable default layout layer while glyph outlines and horizontal advances remain variable.

## OpenType behavior

- Default punctuation is CJK-oriented.
- Default `U+2014` uses the Zhudou-derived CJK form.
- Repeated `U+2014` uses `ccmp` to form continuous two-em/three-em dashes.
- `ENG` language-system `locl` alternates switch shared punctuation to Hanken-derived forms when language metadata is supplied.
- `vert`, `vrt2`, `vhea`, and `vmtx` are retained for CJK vertical layout.

## Distribution

Prebuilt TTF files are published as GitHub Release assets and are intentionally omitted from normal Git history.
