# omp-desktop-zh

An independent fork of [OMP Desktop](https://github.com/apoc/omp-desktop) by apoc (Miroslav Drbal)
with a **Simplified Chinese interface**.

The app itself is unchanged: it is the Tauri 2 desktop front end for the
[oh-my-pi](https://github.com/can1357/oh-my-pi) `omp` coding agent, one `omp --mode rpc-ui`
process per tab, reading and writing the usual `~/.omp` configuration and sessions. This fork
adds Chinese UI text and nothing else.

Both upstream projects are MIT licensed; see [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).

## Why a fork instead of a language pack

Upstream has no i18n: UI strings live inline in the React sources, and release builds compile the
frontend ahead of time and **embed it inside the Rust binary** (the shipped `Contents/Resources`
holds only `icon.icns`). There is no language file to drop in and no way to patch a binary build,
so the only route to a translated UI is rebuilding from a translated source tree.

## What changed

- **`localization/zh.json`** — a 481-entry English → Simplified Chinese dictionary keyed by the
  exact upstream source string.
- **`localization/apply.py`** — applies the dictionary. It rewrites *display positions only*:
  JSX text nodes, display props (`label:`/`title:`/`text:`/`hint:`/`message:`/`aria-label:` …),
  `{"strings"}` children, three whitelisted JSX ternary words, and sentence-like bare literals
  (skipping comments, comparisons and object keys). Code semantics are never touched —
  DOM key sentinels such as `"Dead"` / `"Unidentified"` and the CSS-class ternaries such as
  `cond ? "on" : ""` are explicitly protected.
- **`localization/patch-config.py`** — the three non-text changes: `lang="zh-CN"`, a CJK font
  fallback in the font stacks, and the updater `endpoints` emptied so this build is not silently
  replaced by the official English release. (The `plugins` block itself must stay: the Rust side
  still initializes the updater plugin, and removing its config makes the app panic at startup.)
- Result: **386 dictionary keys / 527 replacements across 57 files**, plus the config edits.

Persistent English by design: the product name, omp tool names (`read`, `bash`, `todo` …),
transcript role labels, and the built-in `default` omp profile name (it comes from profile data,
not from UI text).

## Build (macOS, Apple Silicon verified)

```bash
brew install node rust
npm install
npm run build -- --bundles app      # runs scripts/build-frontend.mjs, then cargo build
cp -R "src-tauri/target/release/bundle/macos/OMP Desktop.app" /Applications/
xattr -dr com.apple.quarantine "/Applications/OMP Desktop.app"
```

`omp` must be on `PATH` (the app also searches Homebrew, `~/.local/bin` and `~/.cargo/bin`).
Builds are ad-hoc signed, not notarized — macOS will want the quarantine flag cleared once.

## Keeping up with upstream

Upstream releases every day or two, so the dictionary needs a refresh now and then:

```bash
git remote add upstream https://github.com/apoc/omp-desktop.git  # once
git fetch upstream && git rebase upstream/HEAD                   # or merge, resolving src/ conflicts by re-applying
python3 localization/apply.py . --dry-run --stats                # keys with 0 hits = strings upstream changed or added
# update localization/zh.json for those, then:
bash localization/build-and-install.sh
```

`--dry-run` lists every dictionary key that no longer matches the source, which is exactly the
work list. See [localization/HOWTO.md](localization/HOWTO.md) for the details and the rollback
steps.

## Status

Verified locally on macOS 27 / Apple Silicon: 52 JSX files compile, `tauri build` succeeds
(`OMP Desktop.app`, ~10.3 MiB), the app launches without crashing, and the rendered UI reads
Chinese in the sidebar, status bar and ambient rail (`项目 / 打开 / 最近 / 已连接 / 成本 /
自动保存 开 / 环境 / 吞吐 / 智能体雷达 / 子智能体 / 空闲 / 小地图 / 命令面板`).
Conversation views, settings and dialogs were not checked screen by screen, and the app's
connection to a real `omp` session was not exercised. Not affiliated with or endorsed by the
upstream author.

## 中文说明

这是 [OMP Desktop](https://github.com/apoc/omp-desktop) 的独立分支，界面为简体中文。
上游没有 i18n，且发布包把前端嵌进了 Rust 二进制，所以汉化只能从源码重建：
`localization/zh.json` 是 481 条英→中字典，`localization/apply.py` 只改「展示位置」的字符串，
绝不碰代码语义字符串。构建方式见上文，上游更新后用 `apply.py --dry-run` 列出失配条目补齐即可。

## License

MIT, same as upstream. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
