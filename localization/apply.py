#!/usr/bin/env python3
"""把 zh.json 里的英文 UI 文案替换成中文（apoc/omp-desktop 汉化）。

用法：
    python3 apply.py <clone 路径> [--dry-run] [--stats]

只改「展示位置」，绝不碰代码语义字符串。四类替换：

  A1. JSX 文本节点        >  文案  <
  A2. 展示型字段的值      label:/title:/text:/hint:/name:/description:/body:/
                          message:/summary:/note:/placeholder:/aria-label:/
                          group:/caption:/empty:/tooltip:/subtitle:
  A3. JSX 表达式子节点    {"文案"}
  B.  裸字面量（仅当「像句子」：含空格或以标点结尾；跳过注释、比较运算、对象键）
      危险名单（DOM key 名 / 哨兵值 / 枚举）永不替换。
"""
import json, re, sys, pathlib, collections

clone = pathlib.Path(sys.argv[1]).expanduser()
dry = "--dry-run" in sys.argv
stats = "--stats" in sys.argv
zh = json.loads(pathlib.Path(__file__).with_name("zh.json").read_text(encoding="utf-8"))
zhx = {k: v for k, v in zh.items()}

NEVER = {"Dead", "Unidentified", "Text", "Binary", "Process", "Ask", "View", "Agent",
         "Model", "Mode", "Tabs", "Session", "Custom", "Added", "Unchanged", "Untracked",
         "Confirm", "Cancel", "Close", "Stop", "Steer", "Deny", "Approve", "Submit",
         "Send", "Retry", "Save", "Delete", "Search", "Next", "Back", "New", "Done",
         "Settings", "Apply", "History", "Changes", "Usage", "Queue", "Context", "Chat",
         "Thinking", "Tokens", "Cost", "Speed", "Branch", "Worktree", "Providers", "Plan",
         "Skills", "Slash", "Commands", "Layout", "Look", "Tweaks"}

DISPLAY_FIELD = (r"(?:label|title|text|hint|description|body|message|summary|note|"
                 r"placeholder|aria-label|group|caption|empty|tooltip|subtitle|verb|statusText|"
                 r"aria-description|labelText|emptyText)")
JSX_TEXT_RE = re.compile(r">(\s*)([^<>{}]+?)(\s*)(?=<|\{)")
JSX_EXPR_RE = re.compile(r"\{\s*\"([^\"\\]*?)\"\s*\}")
FIELD_RE = re.compile(r"(\b" + DISPLAY_FIELD + r"\s*:\s*)([\"'])(.*?)\2")
ATTR_RE = re.compile(r"(\b(?:label|title|text|hint|description|placeholder|aria-label|aria-description|alt|group|caption|tooltip|subtitle)\s*=\s*)([\"'])(.*?)\2")
TERNARY_RE = re.compile(r"(\?|:)\s*\"([^\"\\\n]{1,40})\"")
TERNARY_OK = {"Stop", "Submit", "Steer", "steer", "Ask", "Close", "Cancel", "Save", "Retry",
              "Send", "Back", "Done", "Apply", "Delete", "New", "Next", "Search", "Confirm",
              "Approve", "Deny", "Open with", "Stopped.", "Renamed", "idle"}
# 精确片段替换（唯一形态、无歧义）：自动保存开关的 on/off 不能进三元白名单，
# 因为它同时被用作 CSS 类名（`sidebarOpen ? "on" : ""`），那样会改坏样式。
EXACT = [('? "on" : "off"', '? "开" : "关"'),
         ('cost ${ctx.cost}', '成本 ${ctx.cost}')]   # 右轨卡片是模板字符串，其它 pass 不覆盖


def sentencey(s: str) -> bool:
    return (" " in s) or s.rstrip().endswith(("…", "!", "?", ".", ":", "→", "—", "↗", "↵"))


def comment_spans(text):
    return [(m.start(), m.end()) for m in re.finditer(r"//[^\n]*|/\*.*?\*/", text, re.S)]


def in_spans(pos, spans):
    return any(a <= pos < b for a, b in spans)


def transform(text, counts, fname):
    def bump(k):
        counts[k] += 1

    # A1 JSX 文本节点（尾随的 < 或 { 由前瞻断言保留，不在替换里补）
    def a1(m):
        s = m.group(2).strip()
        if s in zhx:
            bump(s)
            return ">" + m.group(1) + zhx[s] + m.group(3)
        return m.group(0)
    text = JSX_TEXT_RE.sub(a1, text)

    # A2 展示型字段
    def a2(m):
        if m.group(3) in zhx:
            bump(m.group(3))
            return m.group(1) + m.group(2) + zhx[m.group(3)] + m.group(2)
        return m.group(0)
    text = FIELD_RE.sub(a2, text)

    # A3 {"文案"}
    def a3(m):
        if m.group(1) in zhx:
            bump(m.group(1))
            return '{"' + zhx[m.group(1)] + '"}'
        return m.group(0)
    text = JSX_EXPR_RE.sub(a3, text)

    # A4 JSX 展示型属性  title="文案" / placeholder="文案" / aria-label="文案" / alt="文案"
    def a4(m):
        if m.group(3) in zhx:
            bump(m.group(3))
            return m.group(1) + m.group(2) + zhx[m.group(3)] + m.group(2)
        return m.group(0)
    text = ATTR_RE.sub(a4, text)

    # A5 JSX 里的三元展示分支：{cond ? "开始目标" : "Stop"} 这类单个单词
    # 只对白名单里的词生效，且只在 .jsx 里，避免误伤代码里的枚举赋值
    if fname.endswith(".jsx"):
        def a5(m):
            word = m.group(2)
            if word in TERNARY_OK and word in zhx:
                bump(word)
                return m.group(1) + '"' + zhx[word] + '"'
            return m.group(0)
        text = TERNARY_RE.sub(a5, text)

    # A6 少量已知的精确片段（开关类），逐字替换并计数
    for old, new in EXACT:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            for _ in range(n):
                bump("EXACT:" + old)

    # B 裸字面量
    spans = comment_spans(text)
    for key, val in zhx.items():
        if key in NEVER or not sentencey(key) or key not in text:
            continue
        out, last, n = [], 0, 0
        for m in re.finditer(r"([\"'])" + re.escape(key) + r"\1", text):
            if in_spans(m.start(), spans):
                continue
            pre = text[max(0, m.start() - 24):m.start()]
            if re.search(r"(===|!==|==|case\s*)\s*$", pre):
                continue
            post = text[m.end():m.end() + 4]
            if re.match(r"\s*:", post) and re.search(r"(^|[{,(\n])\s*$", pre):
                continue                          # 对象键 / 映射表的键位置
            out.append(text[last:m.start()] + m.group(1) + val + m.group(1))
            last = m.end(); n += 1
        if n:
            text = "".join(out) + text[last:]
            for _ in range(n):
                bump(key)
    return text


total = collections.Counter()
files = [p for p in sorted((clone / "src").rglob("*"))
         if p.suffix in (".js", ".jsx") and not re.match(r"src/(react|marked|highlight|babel)", str(p.relative_to(clone)))]
for f in files:
    text = f.read_text(encoding="utf-8")
    new = transform(text, total, str(f))
    if new != text and not dry:
        f.write_text(new, encoding="utf-8")

untouched = [k for k in zh if k not in total]
print(f"扫描 {len(files)} 个文件 | 字典 {len(zh)} 条 | 命中 {len(total)} 条 / {sum(total.values())} 处" + ("（dry-run）" if dry else "（已写盘）"))
print(f"未命中 {len(untouched)} 条 -> " + ", ".join(untouched[:30]))
if stats:
    for k, v in total.most_common(25):
        print(f"  {v:3d}  {k}")
