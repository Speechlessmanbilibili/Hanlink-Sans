# Hanlink Sans

**语言：** [English](README.md) | 简体中文

**Hanlink Sans** 是专为中西文混排设计的一套无衬线字体家族。它将 Hanken
Grotesk 的西文设计与 Noto Sans SC 的 CJK 覆盖合并，再通过 CJK Punct
Bridge 提供按语言切换的区域标点。

一个家族、一次字体选择，即可在浏览器、设计软件与 Microsoft Word/Office 中
获得顺畅的中西文混排体验。

## 版本状态

**v1.2.2 是当前推荐的稳定版，也是主分支当前采用的构建范围。**

`v1.3.0`、`v1.3.1`、`v1.3.2` 的标签、Release 文件、提交历史与功能说明
全部保留，但这些版本现归类为实验版，并已撤回稳定版推荐。v1.3 的区域字形
与完整谚文扩展使变量字体增长到约 65,214 个字形，`gvar` 表超过 64 MiB；
Microsoft Word/Office 经 Windows GDI 使用这类变量字体时，虽然界面已选择
粗体，实际轮廓仍可能停留在接近默认字重的位置，而非真正的 700 字重。

v1.3 静态字体未复现相同的变量字体故障，但 v1.3 整条版本线均不再作为当前
稳定版推荐。历史版本没有被删除。

## 特性

- **中西文混排一个家族**——无需分别选择拉丁与 CJK 字体。
- **GBK 对齐的汉字**——简体中文及大陆标准繁体字、日文假名、粤语字与注音
  符号，来自固定的 Noto Sans CJK 源（见[覆盖范围](#覆盖范围)）。
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
| CJK 标点 | 经 CJK Punct Bridge 提供 Noto Sans SC/TC/JP/KR 区域形式；中文破折号（`U+2014` 等）来自煮豆黑体 |
| 西文标点 | 共享标点通常使用 Hanken Grotesk；`!`、`?`、`¡`、`¿` 统一改用 Inter 4.001 |
| 全宽问号/感叹号 | `！`、`？` 使用同字重/姿态的 Inter 轮廓，保持 1000 全宽 advance |

当前 v1.2 稳定构建不包含 v1.3 的区域汉字扩展与完整谚文扩展；这些实验功能
的说明保留在下方历史章节和 [FONTLOG.md](FONTLOG.md) 中。

## 下载

从 [GitHub Releases v1.2.2](https://github.com/Speechlessmanbilibili/Hanlink-Sans/releases/tag/v1.2.2)
下载当前推荐稳定版。

| 安装包 | 内容 | 适用场景 |
| --- | --- | --- |
| `Hanlink-Sans-v1.2.2-Static.zip` | 十八个 TTF：九个正体 + 九个斜体，Thin 100 至 Black 900 | Windows、Word/Office，以及对变量字体支持较保守的软件 |
| `Hanlink-Sans-v1.2.2-Variable.zip` | 两个可变 TTF：正体与斜体，`wght` 100–900，默认 400 | 对变量字体支持可靠的浏览器与设计软件 |

斜体家族沿用 Hanken Grotesk 的发布形式：正体与斜体是各自独立的单轴可变
字体，共享 **Hanlink Sans** 家族名。

> 在 Windows 上，静态版与 Variable 版二选一安装，不要同时安装。两者共用
> 家族名 **Hanlink Sans**，同时安装会在字体菜单中产生重复或歧义的字面。

静态家族为非常规/粗体字重提供 Office 兼容的旧式字重链接，同时保留
`Hanlink Sans` 作为排版家族名。

## Hanlink ?!

可选的 interrobang 家族已经在独立仓库
[Speechlessmanbilibili/Hanlink-Interrobang](https://github.com/Speechlessmanbilibili/Hanlink-Interrobang)
维护和发布；本仓库只发布 Hanlink Sans 标准版。

## 使用

安装字体后，选择 **Hanlink Sans** 一个家族即可。网页端：

```css
body {
  font-family: "Hanlink Sans", sans-serif;
  font-feature-settings: "locl" 1;
}
```

在标点地区形式需要区分的场景，请提供准确的语言元数据：

```html
<p lang="zh-CN">简体中文，使用简体中文标点。</p>
<p lang="zh-TW">繁體中文，使用繁體中文標點。</p>
<p lang="ja">日本語の句読点。</p>
<p lang="ko">한국어 문장 부호.</p>
<p lang="en">English punctuation and numerals: 1,234.56.</p>
```

在当前 v1.2 稳定构建中，语言元数据影响**标点形态**，不会扩展文本覆盖范围。
字体无法仅凭周围文字推断共享码点字符的语言；应用或文档必须把语言信息
传递给排版引擎。

## OpenType 行为

- 拉丁文本保留 Hanken Grotesk 特性：`liga`、`dlig`、`case`、`frac`、
  `ordn`、`sups`、`dnom`、`numr`、`ss01`–`ss03`、字距与语言专属 `locl`。
- `locl` 驱动经桥接层提供的区域标点。
- 默认与 CJK 路径的 `U+2014` 使用煮豆派生的中文破折号；重复的 `——` 与
  `———` 经 `ccmp` 形成连续两格/三格破折号。
- 明确的西文语言路径保持独立的 Hanken 破折号，不进行连续合成。
- Noto CJK 布局行为在 Hanken/Noto 字形所有权边界上保留并修复。
- 保留 `vert`、`vrt2`、`vhea` 与 `vmtx` 以支持中文竖排。
- 可变字体由 fontTools varLib 基于经审计的静态母版构建，`wght` 轴
  100–900（正体与斜体各一）。

## 构建与验证

仓库包含完整构建管线、固定源哈希、结构审计、破折号矩阵与 HarfBuzz/RAQM
直接回归。Hanken Grotesk 与 Noto Sans SC 来自 Google Fonts 仓库固定提交；
`Hanlink ?!` 使用固定哈希的 Inter 4.001 正体与斜体变量源。

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

## v1.3 实验历史

- **v1.3.0**：加入台湾、日本、韩国、香港的区域汉字 `locl` 变体；共读取
  25,860 条映射，共享轮廓去重后新增 22,619 个字形。
- **v1.3.1**：恢复 Hanken Grotesk 的 `T+h -> T_h` 等可选连字行为。
- **v1.3.2**：加入 11,172 个谚文音节、兼容谚文字母与 Jamo 区块，并加入
  `Hanlink ?!` 与 Th Grotesk 实验构建脚本。

上述功能、标签和源码仍供研究与归档，但不属于当前稳定构建。

合并策略、精确源版本与发布历史见 [BUILDING.md](BUILDING.md)、
[SOURCES.md](SOURCES.md) 与 [FONTLOG.md](FONTLOG.md)。

## 许可证与命名

Hanlink Sans 以 [SIL Open Font License 1.1](OFL.txt) 分发。它是修改与合并
字体，并非任何上游项目的官方发布。

上游许可证保留 `Source`、`Zhudou` 与 `煮豆` 名称；家族名 **Hanlink Sans**
未使用这些保留名称。署名与随附许可证见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [licenses](licenses/)。
