# Hanlink Sans

**Languages:** English | [简体中文](README.zh-CN.md)

**Hanlink Sans** is a unified sans-serif type family designed for Chinese–English
mixed text. It pairs Hanken Grotesk's Latin design with the Noto Sans CJK
character set, adds language-aware regional punctuation through CJK Punct
Bridge, and — since v1.3.0 — carries regional **glyph variants** for
Traditional Chinese, Japanese, Korean, and Hong Kong Chinese, switched
automatically by document language.

One family, one font selection, for mixed Chinese–English typography in
browsers, design software, and Microsoft Word/Office.

## Features

- **Chinese–Latin mixed text in one family** — no separate Latin/CJK font
  selection; language tags drive both punctuation and glyph forms.
- **GBK-aligned Han ideographs** — Simplified Chinese plus
  mainland-standard Traditional characters, Japanese kana, Cantonese
  characters, and Bopomofo, carried by the pinned Noto Sans CJK source
  (see [Coverage](#coverage)).
- **Regional glyph variants (v1.3.0)** — with `lang="zh-TW"`, `"ja"`,
  `"ko"`, or `"zh-HK"`, Han ideographs automatically switch to the
  corresponding regional forms (Taiwan, Japan, Korea, Hong Kong) through
  OpenType `locl`, exactly as in the four-in-one Noto Sans CJK release.
- **Hanken `dlig` fully restored (v1.3.1)** — the optional `T+h → T_h`
  ligature of Hanken Grotesk (plus all other Hanken discretionary
  ligatures) is preserved in both the static and variable fonts; static
  builds no longer drop the ligature glyphs that the instancer trimmed.
- **Language-aware punctuation** — Simplified/Traditional Chinese, Japanese,
  and Korean punctuation forms selected per language through CJK Punct
  Bridge; explicit Western languages use Hanken Grotesk punctuation.
- **True italic Latin, synthetic italic CJK** — Latin italics use Hanken
  Grotesk's genuine italic designs; CJK italics use a uniform 10-degree
  synthetic slant (no true CJK italic design exists).
- **Full OpenType behavior** — `liga`, `dlig`, `case`, `frac`, `ordn`,
  `sups`, `ss01`–`ss03`, kerning, `locl`, vertical layout (`vert`, `vrt2`,
  `vhea`, `vmtx`), and Zhudou-derived continuous CJK dashes.

## Coverage

Text coverage is Latin plus the pinned Noto Sans CJK character set:

| Script / group | Coverage |
| --- | --- |
| Latin letters and digits `0`–`9` | Hanken Grotesk (digits are Hanken-owned in every language system) |
| Han ideographs | GBK-aligned: Simplified Chinese and mainland-standard Traditional characters, plus regional variants (Taiwan/Japan/Korea/Hong Kong) |
| Japanese kana | Hiragana and katakana (full coverage) |
| Cantonese characters | Common Cantonese written characters (嘅、啲、嚟、咗、喺…) |
| Bopomofo | Full coverage of the 43 phonetic symbols |
| Korean Hangul | **Full coverage (v1.3.2)** — syllables (11,172), compatible jamo letters, and jamo blocks, from the four-in-one Noto CJK source |
| CJK punctuation | Noto Sans SC/TC/JP/KR regional forms through CJK Punct Bridge; Chinese em dashes (`U+2014` and relatives) from Zhudou Sans |
| Western punctuation | Hanken Grotesk for all 46 shared punctuation characters |

The v1.3.0 regional glyph variants cover the differences between
Simplified Chinese and the Taiwan, Japan, Korea, and Hong Kong forms for
25,860 `locl` mappings (shared outlines are deduplicated, adding 22,619
glyphs). Since v1.3.2, Korean Hangul is fully included as well
(11,172 syllables, compatible jamo letters, and jamo blocks), and its
**punctuation** remains localized through the bridge.

## Download

Download the latest release from
[GitHub Releases](https://github.com/Speechlessmanbilibili/Hanlink-Sans/releases/latest).
| Package | Contents | Best for |
| --- | --- | --- |
| `Hanlink-Sans-v1.3.2-Static.zip` | Eighteen TTF faces: nine upright weights plus nine italics, Thin 100 through Black 900 | Any application; static faces are the safest choice for legacy software |
| `Hanlink-Sans-v1.3.2-Variable.zip` | Two variable TTFs with `wght` 100–900, default 400: upright and italic | Modern browsers, design software, and Microsoft Word/Office (variable-font support is well established there) |

The italic family mirrors the pinned Hanken Grotesk release layout:
upright and italic are separate single-axis variable fonts sharing the
**Hanlink Sans** family name.

> On Windows, install either the static family or the variable font, not
> both. They intentionally share the family name **Hanlink Sans**, so
> installing both can create duplicate or ambiguous faces in font menus.

The static family uses Office-compatible legacy weight linking for
non-Regular/Bold faces while retaining `Hanlink Sans` as the typographic
family name.

## Use

After installing the font, select **Hanlink Sans** as a single family. On
the web:

```css
body {
  font-family: "Hanlink Sans", sans-serif;
  font-feature-settings: "locl" 1;
}
```

Provide accurate language metadata whenever punctuation or regional glyph
forms matter:

```html
<p lang="zh-CN">简体中文，使用简体中文标点和字形。</p>
<p lang="zh-TW">繁體中文，使用繁體中文標點與字形。</p>
<p lang="zh-HK">香港繁體，使用港式字形。</p>
<p lang="ja">日本語の句読点と字形。</p>
<p lang="ko">한국어 문장 부호.</p>
<p lang="en">English punctuation and numerals: 1,234.56.</p>
```

Language metadata affects **punctuation shapes** and **regional glyph
variants** only — it does not extend text coverage. A font cannot infer the
language of shared-codepoint characters from surrounding text alone; the
application or document must pass the language to the shaping engine.

## OpenType behavior

- Latin text retains Hanken Grotesk features: `liga`, `dlig`, `case`,
  `frac`, `ordn`, `sups`, `dnom`, `numr`, `ss01`–`ss03`, kerning, and
  language-specific `locl`.
- `locl` drives regional glyph variants for Traditional Chinese, Japanese,
  Korean, and Hong Kong Chinese (v1.3.0), plus regional punctuation through
  the bridge.
- Default and CJK `U+2014` use a Zhudou-derived CJK em dash; repeated
  `——` and `———` form continuous two-em and three-em dashes through `ccmp`.
- Explicit Western-language paths keep repeated em dashes as separate
  Hanken glyphs.
- Noto CJK layout behavior is retained and repaired across the
  Hanken/Noto glyph-ownership boundary.
- `vert`, `vrt2`, `vhea`, and `vmtx` are included for vertical CJK layout.
- The variable fonts are built with fontTools varLib from the audited
  static masters, with a `wght` axis from 100 to 900 (upright and italic).

## Building and verification

The repository contains the complete build pipeline, pinned source hashes,
structural audits, dash matrices, and direct HarfBuzz/RAQM regressions.
All inputs come from immutable upstream releases: Google Fonts repository
files for Hanken Grotesk and the Google Fonts Noto Sans SC distribution,
and the official `googlefonts/noto-cjk` Sans2.004 TTF-VF for regional
glyph variants.

```bash
python scripts/fetch_sources.py
python scripts/build_static_reference.py
HANLINK_ITALIC=1 python scripts/build_static_reference.py
python scripts/build_variable_reference.py
HANLINK_ITALIC=1 python scripts/build_variable_reference.py
python scripts/audit_release.py fonts/static/*.ttf fonts/variable/*.ttf
python scripts/check_dash_matrix.py fonts/static/*.ttf fonts/variable/*.ttf
python scripts/check_han_locl_alignment.py
python scripts/render_regression.py
HANLINK_ITALIC_TEST=1 python scripts/render_regression.py
```

The regional variant pipeline extracts the `locl` mappings of the
four-in-one Noto Sans CJK source (ZHT / JAN / KOR / ZHH), copies the
variant glyphs into Hanlink (deduplicating shared outlines), and installs
a per-language `locl` feature that also carries the existing bridge
punctuation lookups.

See [BUILDING.md](BUILDING.md), [SOURCES.md](SOURCES.md), and
[FONTLOG.md](FONTLOG.md) for the merge strategy, exact source revisions,
and release history.

## 中文简介

Hanlink Sans 的定位是中西文（简体中文与英文）混排排版。西文与 ASCII 数字来自
Google Fonts 的 Hanken Grotesk；汉字（GBK 对齐：简体与大陆标准繁体）、日文
假名、粤语字、注音符号与谚文（v1.3.2 起）来自固定的 Noto Sans CJK 源。
v1.3.0 起，繁体中文、日文、韩文与港式中文的**正文字形**会随语言标签自动
切换为对应地区写法（如 zh-TW 下「骨」「為」自动变为台湾字形），与标点切换
机制同源；v1.3.1 补全 Hanken 的 Th 连字等可选连字。默认与简体中文标点采用
Noto Sans SC，明确的西文语言使用 Hanken 标点。中文破折号采用煮豆派生的
连续形式，并保留竖排替换。

Windows 用户应在静态版和 Variable 版之间二选一，不要同时安装两套同名字体；
两者在 Word/Office 与浏览器中均可正常使用。

## License and naming

Hanlink Sans is distributed under the [SIL Open Font License 1.1](OFL.txt).
It is a modified and combined font, not an official release of any upstream
project.

The upstream licenses reserve the names `Source`, `Zhudou`, and `煮豆`; the
family name **Hanlink Sans** does not use those reserved names. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [licenses](licenses/)
for attribution and bundled licenses.
