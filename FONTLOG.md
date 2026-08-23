# FONTLOG

## 1.001 — 2026-08-23

- Restored Hanken Grotesk Latin OpenType behavior across mixed and Western language systems, including standard/discretionary ligatures, kerning, fractions, ordinals, superscripts/subscripts, stylistic sets, and language-specific `locl`.
- Fixed merged language systems where feature records existed in the font but were not reachable from the active script/language path.
- Reconnected Noto Sans SC `GSUB` and `GPOS` rules across Hanken/Bridge-owned public glyphs while keeping Hanken as the Latin design.
- Fixed post-subset hidden-Noto glyph-name mapping so source lookups reliably target the intended merged glyphs.
- Added script-sensitive remapping for shared Greek, Cyrillic combining-mark, and Bopomofo characters to avoid mixed-source seams.
- Western-script shared punctuation now uses Hanken forms by default through `locl`; explicit Simplified Chinese keeps CJK punctuation.
- English repeated em dashes remain separate Hanken em dashes; default/CJK `——` and `———` retain the continuous Bridge behavior.
- Preserved the shared upstream TrueType `prep` program that was previously removed during subsetting.
- Expanded structural and RAQM rendering regression tests for Hanken, Noto, Bridge, horizontal/vertical dashes, and cross-source layout behavior.

## 1.000 — 2026-08-23

- Initial Hanlink Sans release.
- Combined Hanken Grotesk Latin coverage with Noto Sans SC CJK coverage.
- Integrated CJK Punct Bridge behavior.
- Default `U+2014` changed to the Zhudou-derived CJK form.
- Retained continuous two-em/three-em dash `ccmp` behavior for default/CJK language systems.
- Added English `locl` alternates for ambiguous shared punctuation and disabled the CJK repeated-em-dash `ccmp` path for `ENG`.
- Restored CJK vertical metrics and `vert` / `vrt2`, including dedicated vertical dash forms.
- Fixed the inherited Simplified-Chinese `locl` / `vert` dash-target mapping so horizontal runs cannot receive vertical dash outlines.
- Added regression checks covering `—`, `——`, and `———` in default, `ZHS`, `ENG`, horizontal, and vertical shaping paths.
- Added nine static TTF weights and a `wght` 100–900 variable TTF.
- Family renamed from the development name “Hanken Noto Sans” to **Hanlink Sans** before public packaging.
