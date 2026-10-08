#!/usr/bin/env python3
"""汉化的三处非文案改动（上游更新后需要重做）。

用法：python3 patch-config.py <clone 路径>

1. src/index.html            lang="en" → lang="zh-CN"
2. src/design/styles.css     字体栈补 CJK 回退（本机无 PingFang SC，用 Hiragino Sans GB / Songti SC）
3. src-tauri/tauri.conf.json 删掉 "plugins" 块（含 updater）——
   否则中文构建会被官方英文版通过 updater 自动覆盖
"""
import pathlib, re, sys

clone = pathlib.Path(sys.argv[1]).expanduser()
done = []

html = clone / "src/index.html"
t = html.read_text()
new = t.replace('<html lang="en">', '<html lang="zh-CN">')
html.write_text(new)
lang = re.search(r'<html lang="[^"]+">', new).group(0)
done.append("index.html: " + lang)

css = clone / "src/design/styles.css"
t = css.read_text()
subs = [
    ('"SF Pro Display", sans-serif;', '"SF Pro Display", "Hiragino Sans GB", "Songti SC", sans-serif;'),
    ('"SF Mono", Menlo, monospace;', '"SF Mono", Menlo, "Hiragino Sans GB", monospace;'),
]
for a, b in subs:
    if a in t and b not in t:
        t = t.replace(a, b, 1)
css.write_text(t)
done.append("styles.css: font stack + CJK fallback")

conf = clone / "src-tauri/tauri.conf.json"
raw = conf.read_text()
if '"updater"' in raw:
    # 不能整块删掉：Rust 端仍然 .plugin(tauri_plugin_updater::…)，
    # 配置缺了 plugins.updater 会启动 panic（invalid type: null, expected struct Config）。
    # 正确做法＝保留块、清空 endpoints：中文构建不再被官方英文版自动替换。
    new_raw = re.sub(r'"endpoints":\s*\[[^\]]*\]', '"endpoints": []', raw, count=1)
    conf.write_text(new_raw)
    done.append("tauri.conf.json: updater endpoints 已清空（不再自动更新为英文版）")
else:
    done.append("tauri.conf.json: 没有 updater 块（跳过）")

print("\n".join(done))
