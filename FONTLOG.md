# FONTLOG

## 1.100 — 2026-08-24

- Expanded Western punctuation from eight ambiguous marks to all 46 code points shared by CJK Punct Bridge and the pinned Google Fonts Hanken Grotesk source.
- Made Hanken ownership of ASCII digits invariant across every default, Western, and CJK language system, with direct outline/metric, `locl`, and HarfBuzz regressions.
- Added explicit Hanken punctuation `locl` paths for the configured registered Western languages under Common, Latin, Cyrillic, and Greek runs while restoring Noto SC as every no-language punctuation default.
- Preserved corresponding Noto punctuation for Simplified/phonetic Chinese, Traditional Chinese including Hong Kong and Macao, Japanese, Korean, and old Hangul.
- Split the Noto-shared `U+00B7`/`U+2022` bridge inputs so their distinct Hanken designs remain individually addressable.
- Replaced the compressed layout-compatibility payload with readable source code and made build-cache reuse opt-in to prevent stale release binaries.
- Removed unmergeable source-specific `BASE` variation stores at the documented merge boundary while retaining audited Noto metrics, GSUB/GPOS, and vertical tables.
- Restored the byte-identical Google Fonts Hanken/Noto TrueType `prep` program after merge rather than relying on merger table retention.
- Kept Bridge-to-Hanken repair scoped to direct substitutions and language-specific contexts; HarfBuzz's `frac` normalization remains responsible for converting ASCII slash to the Hanken fraction slash.
- Fixed layout-reference scanning to traverse dictionary-backed single substitutions, allowing Hanken `frac` to reconnect the Bridge-owned ASCII slash to the original fraction glyph.
- Inserted direct Bridge-input repair lookups ahead of the global source lookup list, matching OpenType's global lookup ordering so contextual consumers see repaired glyphs in time.
- Extended direct repairs across every reachable Bridge/Noto `locl` intermediate, preventing an earlier punctuation localization from bypassing Hanken features such as `frac`.
- Ordered Hanken feature repair after final Western `locl` installation so the repair graph includes the Hanlink-specific hidden-Hanken target as well as upstream bridge intermediates.
- Sorted merged GSUB/GPOS FeatureRecords and remapped every LangSys/FeatureVariations index, fixing shapers that require the OpenType-mandated tag order to find the intended private `locl` feature.
- Replaced manual GID-based `gvar` grafting with a nine-master varLib designspace built from the audited static family, eliminating point-topology corruption in the variable font.
- Added direct HarfBuzz shaping comparisons for source advances, clusters, and offsets; RAQM remains the rendering smoke test and is no longer used as a source-metric oracle.
- Added a reproducible source fetcher that downloads Noto Sans SC and Hanken Grotesk only from pinned Google Fonts commits, verifies hashes, and generates the static source instances.
- Expanded structural audits and dash matrices across the full language/punctuation policy.
- Changed RAQM regressions to require successful rendering and matching shaped advances, while the structural audit now compares every Hanken-owned public glyph and all 46 localized punctuation targets directly against the pinned Google Fonts outlines and metrics. This avoids treating deliberate global Noto raster metrics as Hanken outline regressions.
- Replaced inherited upstream identity fields with explicit project authorship, modification copyright, source attribution, repository links, OFL details, and a project-aligned internal revision in every static and variable font.

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
