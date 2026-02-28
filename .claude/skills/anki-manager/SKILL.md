---
name: anki-manager
description: |
  みんなの日本語 Anki 卡包管理助手。通过 AnkiConnect API 操作卡片的增删改查。

  功能：
  1. 添加新单词到 Anki（带 furigana、音调、词性、中文释义）
  2. 批量填充/更新例句和例句翻译
  3. 生成例句 TTS 音频（VOICEVOX WhiteCUL 楽しい）
  4. 更新卡片模板样式（CSS）
  5. 查询/统计卡片状态
  6. 管理两个 Profile（szmz / czh）同步
  7. 文法卡包管理（語法認識 + 選択問題）
  8. SRS 复习策略配置（百词斩风格 / 大间隔低频）

  触发词：
  - "添加单词"、"加词"、"新词" → 添加新单词到 Anki
  - "填例句"、"补例句"、"生成例句" → 批量填充例句
  - "例句音频"、"TTS"、"生成语音" → 生成例句 TTS 音频
  - "更新样式"、"改CSS"、"卡片样式" → 修改卡片模板/CSS
  - "查卡片"、"统计"、"卡片状态" → 查询统计
  - "同步profile"、"同步czh" → 跨 Profile 同步
  - "文法"、"语法"、"grammar" → 文法卡包操作
  - "复习设置"、"SRS"、"间隔" → SRS 配置
version: 2.0.0
allowed-tools: Read, Write, Edit, Bash(python *), Bash(python3 *), Bash(curl *), Bash(cp *), Bash(ls *), Bash(wc *), Bash(grep *), Bash(cat *), Bash(mkdir *), Bash(bash *)
---

# Anki 卡包管理助手

## 架构概览

```
anki/
├── import_apkg.py          # 単語卡包首次导入（blank.apkg → Anki）
├── add.py                  # 补充新单词（補充単語 deck）
├── fill_minna_examples.py  # 从 JSON 填充例句到単語卡
├── tts_minna_examples.py   # 例句 TTS（WhiteCUL 楽しい）
├── unlock.py               # 解锁中文→日文卡片
├── config.py               # SRS 复习策略配置（百词斩 / 大间隔）
├── update_theme.py         # 更新卡片 CSS 样式
├── sync.py                 # 两 Profile 同步
├── parse_grammar.py        # 文法.md → grammar_data.json
├── generate_grammar_quiz.py  # 选择题模板生成 + 检查
├── create_grammar_deck.py  # 文法卡包创建 + 导入
├── examples/               # 每课例句 JSON（lesson_01~50.json）
├── grammar/                # 文法数据
│   ├── grammar_data.json   # 139 个语法点（解析自文法.md）
│   └── grammar_quiz.json   # 选择题数据（手工编辑）
├── blank.apkg              # 源数据（2387 词 + 2263 音频）
└── legacy/                 # 旧版脚本
```

## 牌组结构

| 牌组 | Model | 内容 |
|------|-------|------|
| `みんなの日本語初级1-2 単語` | `みんなの日本語` | 2387 词，按课分子牌组 |
| `補充単語` | `みんなの日本語` | 补充词汇，同字段结构 |
| `みんなの日本語初级1-2 文法` | `文法認識` / `文法選択` | 139 语法点，按课分子牌组 |

子牌组格式：`みんなの日本語初级1-2 文法::第01課`

## AnkiConnect API 基础

所有操作通过 AnkiConnect (localhost:8765) 进行。标准调用模板：

```python
import json, urllib.request, os, time

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"

def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")
```

### 常用 API

| Action | 用途 | 示例 |
|--------|------|------|
| `findNotes` | 查找笔记 | `anki("findNotes", query='"deck:みんなの日本語初级1-2 単語"')` |
| `notesInfo` | 获取笔记详情 | `anki("notesInfo", notes=[nid1, nid2])` |
| `updateNoteFields` | 更新字段 | `anki("updateNoteFields", note={"id": nid, "fields": {...}})` |
| `addNotes` | 批量添加 | `anki("addNotes", notes=[...])` |
| `storeMediaFile` | 存储媒体 | `anki("storeMediaFile", filename="x.wav", data=base64_str)` |
| `modelStyling` | 获取 CSS | `anki("modelStyling", modelName="みんなの日本語")` |
| `updateModelStyling` | 更新 CSS | `anki("updateModelStyling", model={"name": "...", "css": "..."})` |
| `loadProfile` | 切换 Profile | `anki("loadProfile", name="czh")` |
| `getDeckConfig` | 获取牌组选项 | `anki("getDeckConfig", deck="...")` |
| `saveDeckConfig` | 保存牌组选项 | `anki("saveDeckConfig", config={...})` |
| `cloneDeckConfigId` | 创建选项组 | `anki("cloneDeckConfigId", name="文法", cloneFrom=1)` |
| `setDeckConfigId` | 分配选项组 | `anki("setDeckConfigId", decks=[...], configId=n)` |

## Profile 切换（关键！）

`loadProfile` 是**异步**的。API 返回时数据库尚未就绪。

```python
PROFILES = ["szmz", "czh"]

def switch_profile(name):
    try:
        anki("loadProfile", name=name)
    except:
        pass
    time.sleep(10)  # 必须等待！10s 是底线
    # 等 AnkiConnect 在线
    for _ in range(30):
        try:
            anki("version")
            break
        except:
            time.sleep(1)
    # Sanity check
    nids = anki("findNotes", query='"deck:みんなの日本語初级1-2 単語"')
    print(f"  {name}: {len(nids)} notes")
    return nids
```

**已知 note 数量**：szmz ≈ 2387, czh ≈ 2309（単語 deck）。如果切换后数量不对，说明切换失败。

## Deck 和 Model 结构

### 単語 Model: `みんなの日本語`

| 字段 | 说明 | 示例 |
|------|------|------|
| 日文 | furigana 格式 | ` 食[た]べます` |
| 中文 | 释义 | `吃` |
| 词性 | 品词 | `動Ⅱ` |
| 課 | 课号 | `第6課` |
| 音频 | 单词音频 `[sound:file.mp3]` | |
| 基本形 | 基本形 furigana | ` 食[た]べる` |
| 音调核 | 数字 | `2` |
| 外来语 | 外来语原文 | `coffee` |
| 例句 | furigana 格式例句 | ` 朝[あさ]ごはんを 食[た]べます。` |
| 例句翻译 | 中文翻译 | `吃早饭。` |
| 例句音频 | **纯文件名**（不带 `[sound:]`） | `tts_wcul_abc123.wav` |

**注意：例句音频字段存纯文件名，不带 `[sound:]`**。模板用 JS `playEx()` 点击播放。

### 文法 Model 1: `文法認識`

| 字段 | 说明 |
|------|------|
| 正面 | 课号+句型名（JS 隐藏课号前缀） |
| 代表例句 | 第一句例句 HTML |
| 背面 | 中文说明 |
| 例句一覧 | 全部例句 HTML |
| 課 | 课号标签 |

正面：句型名大字 + 一句例句 → 背面：中文说明 + 全部例句

### 文法 Model 2: `文法選択`

| 字段 | 说明 |
|------|------|
| 問題 | 题干（含 `___` 空位） |
| 選択肢A~D | 4 个选项 |
| 正解 | 正确答案（A/B/C/D） |
| 解説 | 翻面解说 |
| 課 | 课号标签 |

多邻国风 4 选 1，背面 JS 高亮正确答案（绿色）。

## SRS 配置（config.py）

### 百词斩风格（単語）

```python
VOCAB_CONFIG = {
    "new_per_day": 50,
    "learning_steps": [1, 10],       # 1m → 10m
    "graduating_ivl": 1,             # Good 毕业: 1天
    "easy_ivl": 30,                  # Easy: 30天
    "rev_per_day": 100,
    "max_ivl": 180,
}
```

### 大间隔低频（文法）

```python
GRAMMAR_CONFIG = {
    "new_per_day": 20,
    "learning_steps": [1440, 2880, 4320],  # 1d → 2d → 3d
    "graduating_ivl": 7,             # Good 毕业: 7天
    "easy_ivl": 21,                  # Easy: 3周
    "rev_per_day": 50,
    "max_ivl": 365,
    "starting_ease": 3.0,            # 300%
    "ivl_fct": 1.2,                  # 间隔修正 120%
}
```

**V3 调度器注意**：AnkiConnect 的 `saveDeckConfig` 写 `new.learningSteps`/`new.graduatingIvl`，但 V3 调度器读 `new.delays`/`new.ints`。**必须同时写两组字段**。

## Furigana 处理

### strip_furigana（去读音，用于匹配）

```python
import re
def strip_furigana(text):
    text = re.sub(r"\[[^\]]+\]", "", text)  # 删所有 [reading]
    text = text.replace("\u3000", "")        # 删全角空格
    return text.strip()
```

**注意**：不能用 `\S+\[...\]` 贪婪匹配！会在连续 furigana（`先[せん]生[せい]`）上出错。

### clean_for_tts（去读音标记，用于 TTS 输入）

```python
def clean_for_tts(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r" (\S+)\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]", "", text)
    text = re.sub(r"\[sound:[^\]]+\]", "", text)
    return text.strip()
```

## TTS 音频生成（VOICEVOX）

**语音**：WhiteCUL 楽しい（speaker_id 运行时从 `/speakers` 查询）
**文件名**：`tts_wcul_{md5[:10]}.wav`

```python
VOICEVOX_URL = "http://127.0.0.1:50021"

def generate_audio(text, speaker_id):
    encoded = urllib.parse.quote(text)
    req = urllib.request.Request(
        f"{VOICEVOX_URL}/audio_query?text={encoded}&speaker={speaker_id}",
        data=b"", method="POST")
    resp = _opener.open(req)
    query = json.loads(resp.read())
    req = urllib.request.Request(
        f"{VOICEVOX_URL}/synthesis?speaker={speaker_id}",
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    return resp.read()
```

## 例句 JSON 格式

文件位于 `anki/examples/lesson_XX.json`：

```json
{
  "食べます": {"jp": " 朝[あさ]ごはんを 食[た]べます。", "cn": "吃早饭。"},
  "飲みます": {"jp": " 毎朝[まいあさ] コーヒーを 飲[の]みます。", "cn": "每天早上喝咖啡。"}
}
```

**key 必须与 Anki 卡片 `日文` 字段 strip_furigana 后的结果一致**（用汉字形式：`私` 不是 `わたし`）。

## CSS 样式

两个 Model 都使用 Duolingo 风格蓝色主题（`#5b9bd5`）。

**中文字体**：`.meaning-text`、`.meaning-front`、`.example-cn` 用 `Noto Sans SC`（避免 Noto Sans JP 渲染中文大小不一）。

更新 CSS 流程：
1. 修改 `import_apkg.py` 中的 CSS 常量
2. 运行 `python3 anki/update_theme.py`（自动同步到两个 Profile）

## 跨 Profile 媒体文件共享

两个 Profile 的媒体文件夹独立：
- szmz: `~/Library/Application Support/Anki2/szmz/collection.media/`
- czh: `~/Library/Application Support/Anki2/czh/collection.media/`

**共享音频**：直接 cp 复制 wav 文件：
```bash
cp ~/Library/Application\ Support/Anki2/szmz/collection.media/tts_wcul_*.wav \
   ~/Library/Application\ Support/Anki2/czh/collection.media/
```

## 增加新书本（如中级1）的完整流程

当需要新增一本教材（如「中级1」）时，按以下步骤：

### 1. 准备源数据

- 获取教材 PDF/扫描件
- OCR → `中级1/output.md`（可用 textbook-ocr-grammar skill）
- 从 output.md 提取文法部分 → `中级1/文法.md`
- 准备单词 apkg 或单词列表

### 2. 単語卡包

**方案 A：有 apkg 文件**
- 修改 `import_apkg.py` 中 `DECK` 名和 apkg 路径
- 或创建新脚本（如 `import_intermediate.py`），复用相同 Model `みんなの日本語`

**方案 B：从单词列表导入**
- 用 `add.py --file words.txt --lesson 第26課` 批量导入到 `補充単語` deck
- 或创建新 deck（如 `みんなの日本語中级1 単語`）并修改脚本 DECK 常量

### 3. 文法卡包

```bash
# Step 1: 解析文法 → JSON
# 修改 parse_grammar.py 的源文件路径和输出路径
python3 anki/parse_grammar.py

# Step 2: 生成选择题模板
python3 anki/generate_grammar_quiz.py

# Step 3: 手工/AI 编辑 grammar_quiz.json（填写 question/options/answer/hint）

# Step 4: 检查完整性
python3 anki/generate_grammar_quiz.py --check

# Step 5: 导入到 Anki（两个 Profile）
python3 anki/create_grammar_deck.py
```

### 4. 例句 + TTS

```bash
# 生成例句 JSON（每课一个文件）
python3 anki/generate_examples.py

# 填充例句到 Anki 卡片
python3 anki/fill_minna_examples.py

# 生成例句 TTS（需 VOICEVOX 运行）
python3 anki/tts_minna_examples.py
```

### 5. 配置 SRS

- 在 `config.py` 的 `VOCAB_DECKS` / `GRAMMAR_DECK` 中添加新牌组名
- 运行 `python3 anki/config.py`

### 6. 需要修改的文件清单

| 文件 | 修改内容 |
|------|----------|
| `import_apkg.py` 或新脚本 | DECK 名、apkg 路径 |
| `parse_grammar.py` | 源 md 路径、输出 JSON 路径 |
| `create_grammar_deck.py` | DECK 名 |
| `fill_minna_examples.py` | DECK 名、examples 路径 |
| `tts_minna_examples.py` | DECK 名 |
| `config.py` | VOCAB_DECKS / GRAMMAR_DECK 列表 |
| `unlock.py` | DECK 名（如果新牌组也需要解锁） |

## 常见操作流程

### 添加新单词

```bash
python3 anki/add.py 食べる たべる 動II 吃
python3 anki/add.py --file words.txt --lesson 第51課
```

### 批量填例句

```bash
python3 anki/fill_minna_examples.py                  # 全部
python3 anki/fill_minna_examples.py --lessons 1-5    # 指定课
python3 anki/fill_minna_examples.py --dry-run        # 预览
```

### 生成例句 TTS

```bash
python3 anki/tts_minna_examples.py                   # 全部
python3 anki/tts_minna_examples.py --profile szmz    # 单个 profile
python3 anki/tts_minna_examples.py --dry-run         # 预览
```

### 更新 CSS 样式

```bash
python3 anki/update_theme.py    # 自动同步两个 Profile
```

### 配置 SRS 选项

```bash
python3 anki/config.py          # 应用到两个 Profile 的所有牌组
```

## 注意事项

1. **必须先确认 Anki 和 VOICEVOX 在线** 再执行操作
2. **Profile 切换后必须 sleep(10)** + sanity check
3. **例句音频字段存纯文件名**，不带 `[sound:]`
4. **strip_furigana 不能用贪婪 \S+**，要先删 `[...]` 再删空格
5. **两个 Profile 的 CSS / 媒体文件独立**，修改后需要同步到另一个
6. **V3 调度器 config 写入需同时更新两组字段**（delays+ints 和 learningSteps+graduatingIvl）
7. **文法牌组用独立选项组「文法」**，通过 `cloneDeckConfigId` + `setDeckConfigId` 管理
