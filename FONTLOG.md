# FONTLOG

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
