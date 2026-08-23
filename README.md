# Hanlink Sans

**Hanlink Sans** is a combined CJK sans-serif family designed for mixed Chinese/Latin text and Microsoft Word/Office use.

- Latin letters, ordinary Western numbers and most Western symbols: **Hanken Grotesk**.
- Han/CJK coverage: **Noto Sans SC**.
- CJK punctuation: Noto Sans SC-based punctuation bridge.
- `U+2014 —` defaults to a Zhudou-derived CJK form; repeated `——` / `———` uses continuous two-em / three-em dash forms.
- With an `ENG` OpenType language system, ambiguous shared punctuation (`· – — ‘ ’ “ ” …`) can switch to Hanken Grotesk through `locl`.
- CJK vertical metrics and `vert` / `vrt2` are retained. The dash family also has dedicated vertical forms.

本字体面向中西文混排和 Word 使用：西文主体取自 Hanken Grotesk，中文主体取自 Noto Sans SC；中文标点默认采用 Noto Sans SC 风格，破折号采用煮豆派生的连续形式，并保留竖排替换。

## Downloads

Prebuilt fonts are distributed through **GitHub Releases** rather than committed directly to the source repository. Release assets include:

- nine static TTF weights, Thin 100 through Black 900;
- one variable TTF with `wght` 100–900, default 400.

The static and variable builds share the typographic family name **Hanlink Sans**. For Windows/Office compatibility, static non-Regular/Bold faces use the conventional legacy nameID 1 weight-linking scheme while all faces use `Hanlink Sans` as typographic family nameID 16.

### Installation note

Do **not** install the static family and the variable font at the same time on Windows. Because they deliberately share the same family name, font enumeration can treat them as duplicate faces. Choose either the static family or the variable TTF.

## OpenType behavior

- Default CJK punctuation comes from Noto Sans SC.
- Default `U+2014` and continuous 2/3-em dash outlines are Zhudou-derived.
- `ccmp` joins repeated `U+2014` into continuous dash glyphs.
- `locl` provides an `ENG` path for shared punctuation using Hanken forms when the application supplies English language metadata.
- `vert` / `vrt2` and `vhea` / `vmtx` are included for vertical CJK layout.
- The variable build uses the Regular vertical metrics across the weight axis.

Language-aware forms depend on the application supplying language information. A font cannot reliably infer whether a shared-codepoint quotation mark or em dash is Chinese or English from surrounding text alone.

## License and naming

Hanlink Sans is licensed under the **SIL Open Font License 1.1 (OFL-1.1)**. It is a modified/combined font and is **not** an official release of any upstream project.

Upstream Reserved Font Names present in the supplied licenses are `Source`, `Zhudou`, and `煮豆`. The primary family name **Hanlink Sans** does not use those reserved names. See `OFL.txt` and `THIRD_PARTY_NOTICES.md`.

## Building

The repository includes reference build scripts and source archive hashes in `SOURCES.md`.
