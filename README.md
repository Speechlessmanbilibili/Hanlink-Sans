# Hanlink Sans

**Languages:** English | [简体中文](README.zh-CN.md)

**Hanlink Sans is a unified sans-serif family for Chinese and Latin mixed text.** It combines Hanken Grotesk's Western design with Noto Sans SC's CJK coverage, then adds language-aware regional punctuation through CJK Punct Bridge.

The result is a single family that works in browsers, design software, and Microsoft Word/Office without requiring separate Latin and CJK font selections.

## Release status

**v1.2.2 is the current recommended stable release and active build scope.**

The `v1.3.0`, `v1.3.1`, and `v1.3.2` tags, release assets, source history,
and feature descriptions are retained for reference, but those releases are
classified as experimental and withdrawn from the stable recommendation.
Their regional-variant and full-Hangul expansion pushed the variable fonts to
about 65,214 glyphs and the `gvar` table beyond 64 MiB. In Microsoft
Word/Office through Windows GDI, selecting Bold can then leave the rendered
outline near the default weight instead of using the true 700 instance.

The v1.3 static faces do not show the same variable-font failure, but the v1.3
line as a whole is no longer recommended. No v1.3 tag or historical description
has been deleted.

## At a glance

| Character group | Design source |
| --- | --- |
| Latin letters | Google Fonts Hanken Grotesk |
| ASCII digits `0`–`9` | Google Fonts Hanken Grotesk in every language system |
| Han ideographs and other Noto-covered scripts | Google Fonts Noto Sans SC |
| Default and Simplified Chinese punctuation | Google Fonts Noto Sans SC, with Zhudou-derived CJK dashes |
| Traditional Chinese, Japanese, and Korean punctuation | Corresponding Google Fonts Noto Sans regional sources through CJK Punct Bridge |
| Explicit Western-language punctuation | Hanken Grotesk for all 46 shared punctuation characters |
| `!`, `?`, `¡`, `¿`, `！`, `？` | Inter 4.001, matched by weight and posture; full-width forms retain 1000-unit advance |

## Download

Download the recommended stable release from
[GitHub Releases v1.2.2](https://github.com/Speechlessmanbilibili/Hanlink-Sans/releases/tag/v1.2.2).

| Package | Contents | Best for |
| --- | --- | --- |
| `Hanlink-Sans-v1.2.2-Static.zip` | Eighteen TTF faces: nine upright weights plus nine italics, Thin 100 through Black 900 | Windows, Word/Office, and applications with conservative variable-font support |
| `Hanlink-Sans-v1.2.2-Variable.zip` | Two variable TTFs with `wght` 100–900, default 400: upright and italic | Modern browsers and applications with reliable variable-font support |

The italic family uses the same release layout as the pinned Hanken Grotesk
upstream: upright and italic are separate single-axis variable fonts sharing
the **Hanlink Sans** family name. In italics, Latin uses Hanken Grotesk's true
italic designs; CJK characters and punctuation use a uniform synthetic
10-degree slant (no true CJK italic design exists).

> On Windows, install either the static family or the variable font, not both. They intentionally share the family name **Hanlink Sans**, so installing both can create duplicate or ambiguous faces in font menus.

The static family uses Office-compatible legacy weight linking for non-Regular/Bold faces while retaining `Hanlink Sans` as the typographic family name.

## Hanlink ?!

The optional interrobang family is maintained and released independently at
[Speechlessmanbilibili/Hanlink-Interrobang](https://github.com/Speechlessmanbilibili/Hanlink-Interrobang).
This repository contains only the standard Hanlink Sans release.

## Use

After installing the font, select **Hanlink Sans** as a single family. On the web:

```css
body {
  font-family: "Hanlink Sans", sans-serif;
  font-feature-settings: "locl" 1;
}
```

Provide accurate language metadata whenever punctuation style matters:

```html
<p lang="zh-CN">简体中文，使用简体中文标点。</p>
<p lang="zh-TW">繁體中文，使用繁體中文標點。</p>
<p lang="ja">日本語の句読点。</p>
<p lang="ko">한국어 문장 부호.</p>
<p lang="en">English punctuation and numerals: 1,234.56.</p>
```

A font cannot infer the language of a shared-codepoint quotation mark, comma, or em dash from surrounding text alone. The application or document must pass the language to the shaping engine for `locl` to select the intended form.

## Language-aware punctuation

| Language or shaping path | Result |
| --- | --- |
| No language / default LangSys | Noto Sans SC punctuation |
| Simplified or phonetic Chinese | Noto Sans SC punctuation |
| Traditional Chinese, including Hong Kong and Macao | Noto Sans TC punctuation |
| Japanese | Noto Sans JP punctuation |
| Korean and old Hangul | Noto Sans KR punctuation |
| Configured explicit Western languages in Common, Latin, Cyrillic, or Greek runs | Hanken Grotesk punctuation where covered |

ASCII digits always retain the original Hanken Grotesk outlines and metrics. Language switching changes punctuation, never `0`–`9`.

## OpenType behavior

- Latin text retains Hanken Grotesk features including `liga`, `dlig`, `case`, `frac`, `ordn`, `sups`, `dnom`, `numr`, `ss01`–`ss03`, kerning, and language-specific `locl`.
- Default and CJK `U+2014` use a Zhudou-derived CJK em dash; repeated `——` and `———` form continuous two-em and three-em dashes through `ccmp`.
- Explicit Western-language paths keep repeated em dashes as separate Hanken glyphs.
- Noto CJK layout behavior is retained and repaired across the Hanken/Noto glyph-ownership boundary.
- `vert`, `vrt2`, `vhea`, and `vmtx` are included for vertical CJK layout.
- The variable font is built with fontTools varLib from nine audited static masters, with a `wght` axis from 100 to 900. The italic variable font is built the same way from the nine italic static masters.
- Italic Latin keeps the Hanken Grotesk Italic design; CJK italics are synthetic 10-degree slants, unhinted but with preserved point structure for interpolation.

## 中文简介

Hanlink Sans 面向中西文混排：西文与 ASCII 数字来自 Google Fonts 的 Hanken Grotesk，汉字主体来自 Google Fonts 的 Noto Sans SC。默认与简体中文标点采用 Noto Sans SC；繁体中文、日文、韩文根据语言信息切换到对应的 Noto 地区字形；明确的西文语言则使用 Hanken 标点。中文破折号采用煮豆派生的连续形式，并保留竖排替换。

Windows 用户应在静态版和 Variable 版之间二选一，不要同时安装两套同名字体。若主要用于 Word/Office，优先选择 Static 包。

## Reproducible builds and verification

The repository contains the complete build pipeline, pinned source hashes, structural audits, dash matrices, and direct HarfBuzz/RAQM regressions. Noto Sans SC and Hanken Grotesk come exclusively from immutable Google Fonts repository files.

```bash
python scripts/fetch_sources.py
python scripts/build_static_reference.py
HANLINK_ITALIC=1 python scripts/build_static_reference.py
python scripts/build_variable_reference.py
HANLINK_ITALIC=1 python scripts/build_variable_reference.py
INTER_VF=sources/inter/InterVariable.ttf python scripts/build_interrobang.py
HANLINK_ITALIC=1 INTER_VF=sources/inter/InterVariable-Italic.ttf python scripts/build_interrobang.py
python scripts/build_variable_interrobang.py
HANLINK_ITALIC=1 python scripts/build_variable_interrobang.py
python scripts/audit_release.py fonts/static/*.ttf fonts/variable/*.ttf
python scripts/check_dash_matrix.py fonts/static/*.ttf fonts/variable/*.ttf
python scripts/render_regression.py
HANLINK_ITALIC_TEST=1 python scripts/render_regression.py
```

See [BUILDING.md](BUILDING.md), [SOURCES.md](SOURCES.md), and [FONTLOG.md](FONTLOG.md) for the merge strategy, exact source revisions, and release history.

## License and naming

Hanlink Sans is distributed under the [SIL Open Font License 1.1](OFL.txt). It is a modified and combined font, not an official release of any upstream project.

The upstream licenses reserve the names `Source`, `Zhudou`, and `煮豆`; the family name **Hanlink Sans** does not use those reserved names. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [licenses](licenses/) for attribution and bundled licenses.
