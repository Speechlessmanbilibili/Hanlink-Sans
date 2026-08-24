# Hanlink Sans

**Hanlink Sans** is a combined CJK sans-serif family designed for mixed Chinese/Latin text and Microsoft Word/Office use.

- Latin letters, ordinary Western numbers and most Western symbols: **Hanken Grotesk from Google Fonts**.
- Han/CJK coverage: **Noto Sans SC from Google Fonts**.
- CJK punctuation: Noto Sans SC-based punctuation bridge.
- `U+2014 —` defaults to a Zhudou-derived CJK form; repeated `——` / `———` uses continuous two-em / three-em dash forms.
- In supported explicit Western languages under Common (`DFLT`), Latin, Cyrillic, or Greek runs, all 46 bridge punctuation code points also covered by Hanken Grotesk switch to Hanken through `locl`. Every default LangSys and all explicit CJK regions keep the corresponding Noto forms.
- ASCII digits `0`–`9` always use the exact Google Fonts Hanken Grotesk outlines and metrics, in every default, Western, and CJK language system. Language switching changes punctuation, never digits.
- CJK vertical metrics and `vert` / `vrt2` are retained. The dash family also has dedicated vertical forms.

本字体面向中西文混排和 Word 使用：西文主体取自 Hanken Grotesk，中文主体取自 Noto Sans SC；中文标点默认采用 Noto Sans SC 风格，破折号采用煮豆派生的连续形式，并保留竖排替换。

## Downloads

Compiled fonts are distributed through GitHub Releases rather than committed to the source repository:

- `Hanlink-Sans-v1.1.0-Static.zip`: nine static TTF weights, Thin 100 through Black 900.
- `Hanlink-Sans-v1.1.0-Variable.zip`: variable TTF, `wght` 100–900, default 400.

The static and variable builds share the typographic family name **Hanlink Sans**. For Windows/Office compatibility, static non-Regular/Bold faces use the conventional legacy nameID 1 weight-linking scheme while all faces use `Hanlink Sans` as typographic family nameID 16.

### Installation note

Do **not** install the static family and the variable font at the same time on Windows. Because they deliberately share the same family name, font enumeration can treat them as duplicate faces. Choose either the static release package or the variable-font release package.

## OpenType behavior

- Default CJK punctuation comes from Noto Sans SC.
- Default `U+2014` and continuous 2/3-em dash outlines are Zhudou-derived.
- `ccmp` joins repeated `U+2014` into continuous dash glyphs on the default/CJK path; explicit Western-language runs keep separate Hanken em dashes.
- Latin runs retain Hanken Grotesk OpenType behavior including `liga`, `dlig`, `case`, `frac`, `ordn`, `sups`, `dnom`, `numr`, `ss01`–`ss03`, kerning, and language-specific `locl`.
- Explicit Western-language punctuation uses Hanken forms through `locl`; no-language script defaults and Chinese SC/TC/HK/Macao/phonetic, Japanese, Korean, and old-Hangul tags keep their corresponding Noto punctuation.
- Noto Sans SC OpenType behavior is retained for CJK and its other covered scripts, including cross-source `GSUB`/`GPOS` repairs where public glyph ownership differs.
- `vert` / `vrt2` and `vhea` / `vmtx` are included for vertical CJK layout.
- The variable build uses the Regular vertical metrics across the weight axis. This is compatible with the source Noto Sans SC VF, which itself does not provide a separate `VVAR` table.

Language-aware forms depend on the application supplying language information. A font cannot reliably infer whether a shared-codepoint quotation mark or em dash is Chinese or English from surrounding text alone.

## License and naming

Hanlink Sans is licensed under the **SIL Open Font License 1.1 (OFL-1.1)**. It is a modified/combined font and is **not** an official release of any upstream project.

Upstream Reserved Font Names present in the supplied licenses are `Source`, `Zhudou`, and `煮豆`. The primary family name **Hanlink Sans** does not use those reserved names. See `OFL.txt`, `THIRD_PARTY_NOTICES.md`, and `licenses/`.

## Building

The repository includes the build scripts, structural regression checks, RAQM rendering regression checks, and pinned source hashes in `SOURCES.md`. Noto Sans SC and Hanken Grotesk are sourced exclusively from fixed files in the Google Fonts repository; `scripts/fetch_sources.py` downloads and verifies them.
