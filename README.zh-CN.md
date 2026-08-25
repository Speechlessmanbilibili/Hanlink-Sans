# Hanlink Sans

**语言：** [English](README.md) | 简体中文

**Hanlink Sans** 是专为中西文（中文与英文）混排设计的一套无衬线字体家族。它
将 Hanken Grotesk 的拉丁字形与 Noto Sans CJK 的字符集结合，通过 CJK Punct
Bridge 提供语言感知的区域标点，并且自 v1.3.0 起内置**区域字形变体**——繁体
中文、日文、韩文与港式中文的字形会随文档语言自动切换。

一个家族、一次字体选择，即可在浏览器、设计软件与 Microsoft Word/Office 中
获得顺畅的中西文混排体验。

## 特性

- **中西文混排一个家族**——无需分别选择拉丁与 CJK 字体；语言标签同时驱动
  标点与字形形态。
- **GBK 对齐的汉字**——简体中文及大陆标准繁体字、日文假名、粤语字与注音
  符号，来自固定的 Noto Sans CJK 源（见[覆盖范围](#覆盖范围)）。
- **区域字形变体（v1.3.0）**——设置 `lang="zh-TW"`、`"ja"`、`"ko"` 或
  `"zh-HK"` 时，汉字通过 OpenType `locl` 自动切换为对应地区写法（台湾、
  日本、韩国、香港），与四地合一的 Noto Sans CJK 行为一致。
- **语言感知标点**——简体/繁体中文、日文、韩文标点按语言经 CJK Punct
  Bridge 切换；明确的西文语言使用 Hanken Grotesk 标点。
- **拉丁真斜体、中文合成斜体**——拉丁斜体采用 Hanken Grotesk 官方斜体
  设计；中文斜体使用统一的 10° 合成斜切（中文没有真斜体设计）。
- **完整 OpenType 行为**——`liga`、`dlig`、`case`、`frac`、`ordn`、`sups`、
  `ss01`–`ss03`、字距、`locl`、竖排（`vert`、`vrt2`、`vhea`、`vmtx`）以及
  煮豆派生的连续中文破折号。

## 覆盖范围

文本覆盖为拉丁文 + 固定的 Noto Sans CJK 字符集：

| 文字 / 分组 | 覆盖情况 |
| --- | --- |
| 拉丁字母与数字 `0`–`9` | Hanken Grotesk（数字在所有语言系统下均由 Hanken 提供） |
| 汉字 | GBK 对齐：简体中文与大陆标准繁体字 |
| 日文假名 | 平假名与片假名（完整覆盖） |
| 粤语字 | 常用粤语书写字（嘅、啲、嚟、咗、喺…） |
| 注音符号 | 43 个注音符号完整覆盖 |
| 谚文（韩文） | **不包含**——回退到系统字体 |
| CJK 标点 | 经 CJK Punct Bridge 提供 Noto Sans SC/TC/JP/KR 区域形式；中文破折号（`U+2014` 等）来自煮豆黑体 |
| 西文标点 | 46 个共享标点字符全部使用 Hanken Grotesk |

v1.3.0 的区域字形变体覆盖简体中文与台湾、日本、韩国、香港写法之间的差异，
共 25,860 条 `locl` 映射（共享轮廓去重后实际新增 22,619 个字形）。谚文
音节不在字符集内；其**标点**仍经桥接层按语言本地化。

## 下载

从 [GitHub Releases](https://github.com/Speechlessmanbilibili/Hanlink-Sans/releases/latest)
下载最新版本。

| 安装包 | 内容 | 适用场景 |
| --- | --- | --- |
| `Hanlink-Sans-v1.3.0-Static.zip` | 十八个 TTF：九个正体 + 九个斜体，Thin 100 至 Black 900 | Windows、Word/Office 及对可变字体支持保守的应用 |
| `Hanlink-Sans-v1.3.0-Variable.zip` | 两个可变 TTF：正体与斜体，`wght` 100–900，默认 400 | 现代浏览器与可变字体支持完善的应用 |

斜体家族沿用 Hanken Grotesk 的发布形式：正体与斜体是各自独立的单轴可变
字体，共享 **Hanlink Sans** 家族名。

> 在 Windows 上，静态版与 Variable 版二选一安装，不要同时安装。两者共用
> 家族名 **Hanlink Sans**，同时安装会在字体菜单中产生重复或歧义的字面。

静态家族为非常规/粗体字重提供 Office 兼容的旧式字重链接，同时保留
`Hanlink Sans` 作为排版家族名。

## 使用

安装字体后，选择 **Hanlink Sans** 一个家族即可。网页端：

```css
body {
  font-family: "Hanlink Sans", sans-serif;
  font-feature-settings: "locl" 1;
}
```

在标点或区域字形需要区分的场景，请提供准确的语言元数据：

```html
<p lang="zh-CN">简体中文，使用简体中文标点和字形。</p>
<p lang="zh-TW">繁體中文，使用繁體中文標點與字形。</p>
<p lang="zh-HK">香港繁體，使用港式字形。</p>
<p lang="ja">日本語の句読点と字形。</p>
<p lang="ko">한국어 문장 부호.</p>
<p lang="en">English punctuation and numerals: 1,234.56.</p>
```

语言元数据只影响**标点形态**与**区域字形变体**——不会扩展文本覆盖范围。
字体无法仅凭周围文字推断共享码点字符的语言；应用或文档必须把语言信息
传递给排版引擎。

## OpenType 行为

- 拉丁文本保留 Hanken Grotesk 特性：`liga`、`dlig`、`case`、`frac`、
  `ordn`、`sups`、`dnom`、`numr`、`ss01`–`ss03`、字距与语言专属 `locl`。
- `locl` 驱动繁体中文、日文、韩文与港式中文的区域字形变体（v1.3.0），
  以及经桥接层的区域标点。
- 默认与 CJK 路径的 `U+2014` 使用煮豆派生的中文破折号；重复的 `——` 与
  `———` 经 `ccmp` 形成连续两格/三格破折号。
- 明确的西文语言路径保持独立的 Hanken 破折号，不进行连续合成。
- Noto CJK 布局行为在 Hanken/Noto 字形所有权边界上保留并修复。
- 保留 `vert`、`vrt2`、`vhea` 与 `vmtx` 以支持中文竖排。
- 可变字体由 fontTools varLib 基于经审计的静态母版构建，`wght` 轴
  100–900（正体与斜体各一）。

## 构建与验证

仓库包含完整构建管线、固定源哈希、结构审计、破折号矩阵与 HarfBuzz/RAQM
直接回归。所有输入均来自不可变的上游发布：Hanken Grotesk 与 Noto Sans SC
来自 Google Fonts 仓库固定提交，区域字形变体来自官方
`googlefonts/noto-cjk` Sans2.004 TTF-VF。

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

区域字形管线从四地合一的 Noto Sans CJK 源提取 `locl` 映射（ZHT / JAN /
KOR / ZHH），将变体字形复制进 Hanlink（共享轮廓去重），并为每个语言安装
独立的 `locl` 特性（同时承载已有的桥接标点查找）。

合并策略、精确源版本与发布历史见 [BUILDING.md](BUILDING.md)、
[SOURCES.md](SOURCES.md) 与 [FONTLOG.md](FONTLOG.md)。

## 许可证与命名

Hanlink Sans 以 [SIL Open Font License 1.1](OFL.txt) 分发。它是修改与合并
字体，并非任何上游项目的官方发布。

上游许可证保留 `Source`、`Zhudou` 与 `煮豆` 名称；家族名 **Hanlink Sans**
未使用这些保留名称。署名与随附许可证见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [licenses](licenses/)。
