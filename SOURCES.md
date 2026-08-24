# Source inputs

Pinned inputs used by v1.2.0. Noto Sans SC and Hanken Grotesk are sourced exclusively from the Google Fonts repository distributions below.

| Input | Pinned source | SHA-256 |
| --- | --- | --- |
| Google Fonts Hanken Grotesk variable TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk[wght].ttf` | `813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f` |
| Google Fonts Hanken Grotesk Italic variable TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk-Italic[wght].ttf` | `ae5731726ff75301a3cb63f2e98d1babc77d55ab09fb8e229ca75f5bd46fbe32` |
| Google Fonts Noto Sans SC variable TTF | `google/fonts@2894aab31764f10f29c421bdfd2340d3b382d384 / ofl/notosanssc/NotoSansSC[wght].ttf` | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| CJK Punct Bridge | `Speechlessmanbilibili/CJK-Punct-Bridge v1.3.0` | Built and audited from its pinned Google Fonts Noto/Hanken inputs and Zhudou v2.000 |

`scripts/fetch_sources.py` contains the immutable Google Fonts URLs, verifies both hashes, and derives the nine static source instances from the pinned variable files. Upstream license and attribution information is summarized in `OFL.txt` and `THIRD_PARTY_NOTICES.md`.

The OpenType language-system policy in `scripts/language_systems.py` uses registered tags from Microsoft's OpenType 1.9 registry, last updated 2024-05-31. It is build metadata only, not a font-outline source.
