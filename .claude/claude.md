## Workflow Rules

Do NOT run git commit commands unless the user explicitly asks for a commit. Do not generate summary reports or post-task recaps unless requested.

## Japanese Study Notes

When adding content to Japanese study notes, always check the existing module structure first. Verb forms go in モジュール2, adjective/noun forms in モジュール3, sentence patterns in モジュール4. Never combine all content into a single module without checking.

## Content Management

Before adding new content to any existing notes file, grep/search for existing coverage of that topic first. Never add duplicate content for lessons or grammar points that already exist.

## Style Preferences

Keep generated content concise unless explicitly asked for detail. For vocabulary supplements and reference tables, default to a single clean table — not verbose explanations. When in doubt, ask before generating long-form output.

## Problem Solving

When an approach fails once, do NOT retry the same approach. Stop and ask the user for guidance or propose a completely different strategy. Especially avoid: OCR on files Claude can't read, fabricating content from memory when source material is available, and installing packages without first verifying they exist.

## AnkiConnect Profile 切换注意事项

**问题根因：`loadProfile` 返回 ≠ Profile 已就绪。**

AnkiConnect 的 `loadProfile` 是异步的——API 返回 `true` 时，Anki 内部仍在关闭旧 Profile、打开新数据库。此时调用 `version` 能成功（AnkiConnect 本身在线），但 `findNotes` / `notesInfo` 读到的可能仍是旧 Profile 的数据。

**实际表现：**
- `sleep(5)` + `version` 检查 → 经常读到旧 Profile 数据（尤其 szmz→czh 方向）
- `sleep(10)` + `version` 检查 → 稳定成功

**脚本中的正确做法：**
1. `loadProfile` 后至少 `sleep(8)`（保守用 `sleep(10)`）
2. `version` 检查只确认 AnkiConnect 在线，不代表 Profile 数据库就绪
3. 切换后先用 `findNotes` 做一次查询并验证返回数量，与预期对比，确认真的切换了
4. 如果两个 Profile 的卡片数不同（如 szmz=2387, czh=2309），可以用 note 数量做 sanity check

**模板代码：**
```python
anki("loadProfile", name=profile)
time.sleep(10)
wait_for_anki(30)
# Sanity check: verify profile actually switched
nids = anki("findNotes", query='"deck:みんなの日本語"')
print(f"  {profile}: {len(nids)} notes")
```

## Anki Furigana 字段匹配

Anki 的 `日文` 字段中，furigana 有两种格式：
- 有空格前缀：` 食[た]べます`（标准）
- 无空格连续：`先[せん]生[せい]`、`電[でん]車[しゃ]`

**旧 strip_furigana 的 bug：** `re.sub(r" ?(\S+)\[...\]", r"\1", text)` 中 `\S+` 贪婪匹配会吞掉前面的 `[...]`，导致 `先[せん]生[せい]` → `先[せん]生`（错误）。

**正确写法：**
```python
def strip_furigana(text):
    text = re.sub(r"\[[^\]]+\]", "", text)  # 先删所有 [reading]
    text = text.replace(" ", "")             # 再删 furigana 标记空格
    return text.strip()
```

另外注意 Anki 词条用的是汉字形式（如 `私` 而非 `わたし`、`貴方` 而非 `あなた`、`鞄` 而非 `かばん`）。生成例句 JSON 的 key 必须与 strip 后的结果一致。
