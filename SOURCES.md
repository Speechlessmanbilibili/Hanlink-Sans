# Source inputs

Pinned inputs used by v1.2.1. Noto Sans SC and Hanken Grotesk are sourced exclusively from the Google Fonts repository distributions below.

| Input | Pinned source | SHA-256 |
| --- | --- | --- |
| Google Fonts Hanken Grotesk variable TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk[wght].ttf` | `813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f` |
| Google Fonts Hanken Grotesk Italic variable TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk-Italic[wght].ttf` | `ae5731726ff75301a3cb63f2e98d1babc77d55ab09fb8e229ca75f5bd46fbe32` |
| Google Fonts Noto Sans SC variable TTF | `google/fonts@2894aab31764f10f29c421bdfd2340d3b382d384 / ofl/notosanssc/NotoSansSC[wght].ttf` | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| CJK Punct Bridge | `Speechlessmanbilibili/CJK-Punct-Bridge v1.3.2` | Built and audited from its pinned Google Fonts Noto/Hanken inputs and Zhudou v2.000 |
| Inter 4.001 upright variable TTF (`Hanlink ?!` only) | Local OFL input `InterVariable.ttf`, internal source revision `git-9221beed3`; set `INTER_VF` or place under `sources/inter/` | `4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf` |
| Inter 4.001 italic variable TTF (`Hanlink ?!` only) | Local OFL input `InterVariable-Italic.ttf`, internal source revision `git-9221beed3`; set `INTER_VF` or place under `sources/inter/` | `d6f1f6a172d9e588438db9f986fd5cfad7b30f644374080a8a9d4d91e344586f` |

`scripts/fetch_sources.py` contains the immutable Google Fonts URLs, verifies both hashes, and derives the nine static source instances from the pinned variable files. Upstream license and attribution information is summarized in `OFL.txt` and `THIRD_PARTY_NOTICES.md`.

Inter is not downloaded by `fetch_sources.py`. The `Hanlink ?!` builder checks
the supplied font's exact SHA-256, version, `opsz`/`wght` axes, and `U+203D`
coverage before using it. The upright and italic hashes above are the only
accepted defaults for the v1.2.1 `?!` release build.

The OpenType language-system policy in `scripts/language_systems.py` uses registered tags from Microsoft's OpenType 1.9 registry, last updated 2024-05-31. It is build metadata only, not a font-outline source.
