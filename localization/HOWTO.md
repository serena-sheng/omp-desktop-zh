# 汉化工具说明（HOWTO）

本仓库是 `apoc/omp-desktop` 的中文分支：`src/` 里已经是汉化后的源码，`localization/` 放的是
「怎么把汉化重新套上去」的工具。上游**没有 i18n**，所以汉化是字典 + 精准替换，不是语言包。

## 目录

| 文件 | 作用 |
|---|---|
| `zh.json` | 英→中字典（481 条）。键 = 上游源码里的原文，**逐字节精确**（含 `…`、`↵` 等） |
| `apply.py` | 把字典应用到 `src/`。**只改展示位置**，可 `--dry-run --stats` 先看命中 |
| `patch-config.py` | 三处非文案改动：`lang="zh-CN"`、字体栈补 CJK、清空 updater `endpoints` |
| `build-and-install.sh` | 应用字典 → 配置改动 → `tauri build` → 装到 `/Applications` |

## 上游更新后怎么重新汉化

```bash
git fetch upstream && git rebase upstream/HEAD     # 冲突多半落在 src/，用下面两步重来
python3 localization/apply.py . --dry-run --stats  # 「未命中」清单 = 上游改过或新增的英文
# 照着清单补 zh.json，然后：
bash localization/build-and-install.sh
```

`apply.py` 的命中数会逐条打印：**0 命中说明上游不再用那句英文**（或改写了），照清单更新即可。

## apply.py 的安全性设计（为什么不会改坏代码）

六类替换，全部限定在「展示位置」：

- **A1** JSX 文本节点 `>文案<`（也覆盖 `文案 {expr}`，靠前瞻断言，注意前瞻不消费字符）；
- **A2** 展示型字段值 `label: "…"` / `title:` / `text:` / `hint:` / `message:` / `placeholder:` / `aria-label:` …；
- **A3** `{"文案"}`；
- **A4** 展示型属性 `title="…"` / `placeholder="…"` / `label="…"` …；
- **A5** 少数 JSX 三元里的单词（**白名单**）；
- **A6** 两个无歧义的精确片段；
- 兜底 **B**：裸字面量，仅当「像句子」（含空格或以标点结尾），且跳过注释、比较运算、对象键位置。

**永不替换**：`Dead` / `Unidentified` 这类 DOM 键名哨兵（`keymap.js` 用它处理死键与未识别键，
翻了键处理就废）；`name:` 字段（图标/资源 id）；同时被用作 CSS 类名的形态（`cond ? "on" : ""`、
`running ? "running" : "ok"`）——这类只能对唯一那处用精确片段替换。

## 配置改动为什么是这三处

1. `lang="zh-CN"`：让 WebView 用对断行/字重；
2. 字体栈补 `"Hiragino Sans GB", "Songti SC"`：macOS 上并非每台机器都有 PingFang SC；
3. **updater `endpoints` 清空**：否则这个中文构建会被官方英文版自动更新掉。
   注意**不能整块删 `plugins`** —— Rust 端仍在 `.plugin(tauri_plugin_updater::…)`，
   配置缺失会启动即 panic（`invalid type: null, expected struct Config`）。

## 构建前置与耗时

`brew install node rust`（rust 会带 llvm 依赖，约 2.4 GB）。首次 `cargo build` 约 5 分钟，
之后增量约 1 分钟。

## 回滚

```bash
git checkout <upstream-tag> -- src src-tauri/tauri.conf.json   # 回到纯英文源码
npm run build -- --bundles app
rm -rf "/Applications/OMP Desktop.app"                          # 或重装官方 dmg
```
