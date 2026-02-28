# みんなの日本語 Anki 工具集

《大家的日语》初级 1-2（第 1-50 课）全套 Anki 学习工具。Duolingo 风格卡片，双人独立复习，通过 AnkiConnect 自动化管理。

## 概览

| 牌组 | 卡片类型 | 数量 | 说明 |
|------|---------|------|------|
| **みんなの日本語初级1-2 単語** | 日文→含義 / 中文→日文 | 2387 词 | 按课分子牌组，含原生音频 |
| **補充単語** | 同上 | ~43 词 | 课外补充词汇 |
| **みんなの日本語初级1-2 文法** | 語法認識 / 選択問題 | 139 语法点 | 按课分子牌组，多邻国风选择题 |

## 卡片设计

### 単語（双方向）

| 卡片 | 方向 | 状态 |
|------|------|------|
| 日文→含義 | 看汉字 → 回忆读音+意思 | 正常学习 |
| 中文→日文 | 看中文 → 回忆日语怎么说 | **默认挂起**，复习 ≥3 次后自动解锁 |

字段：注音假名（furigana）、音调核、词性、基本形、外来语词源、中文释义、例句、例句翻译、例句音频

### 文法（两种卡型）

**語法認識** — 正面：句型名 + 代表例句 → 背面：中文说明 + 全部例句

**選択問題** — 多邻国风 4 选 1，翻面正确答案绿色高亮

## 双人模式

两个 Anki Profile（**szmz** / **czh**），共享同一套词库，**复习进度完全独立**。各自在手机上登录自己的 AnkiWeb 账号同步。

## SRS 复习策略

| 牌组 | 风格 | 学习步骤 | 毕业间隔 | 每日新卡 | 最大间隔 |
|------|------|---------|---------|---------|---------|
| 単語 | 百词斩 | 1m → 10m | 1d | 50 | 180d |
| 文法 | 大间隔低频 | 1d → 2d → 3d | 7d | 20 | 365d |

建议开启 FSRS 算法（Anki GUI → 牌组选项 → FSRS 开关）。

## 前置条件

- [Anki](https://apps.ankiweb.net/) 桌面版
- [AnkiConnect](https://ankiweb.net/shared/info/2055492159) 插件（代码 `2055492159`）
- [VOICEVOX](https://voicevox.hiroshiba.jp/)（仅 TTS 音频生成时需要）

## 使用方法

### 首次导入

```bash
# 単語：同时导入到 szmz 和 czh
python3 anki/sync.py

# 文法：导入到两个 Profile
python3 anki/create_grammar_deck.py

# 配置 SRS 选项
python3 anki/config.py
```

### 日常操作

```bash
# 解锁中文→日文卡片（默认复习 ≥3 次后解锁）
python3 anki/unlock.py

# 补充新单词
python3 anki/add.py 食べる たべる 動II 吃
python3 anki/add.py --file words.txt --lesson 第51課

# 填充例句到卡片
python3 anki/fill_minna_examples.py
python3 anki/fill_minna_examples.py --lessons 1-5

# 生成例句 TTS 音频（需 VOICEVOX 运行）
python3 anki/tts_minna_examples.py

# 更新卡片 CSS 样式
python3 anki/update_theme.py
```

### 文法卡包制作流程

```bash
# 1. 解析文法.md → JSON
python3 anki/parse_grammar.py

# 2. 生成选择题空白模板
python3 anki/generate_grammar_quiz.py

# 3. 手工/AI 编辑 grammar/grammar_quiz.json
#    填写每题的 question / options / answer / hint

# 4. 检查完整性
python3 anki/generate_grammar_quiz.py --check

# 5. 导入到 Anki（两个 Profile）
python3 anki/create_grammar_deck.py
```

## 增加新书本（如中级1）

### Step 1: 准备数据

1. 获取教材 → OCR → `中级1/output.md`
2. 提取文法 → `中级1/文法.md`
3. 准备单词列表或 apkg

### Step 2: 修改脚本

需要修改 DECK 常量的文件：

| 文件 | 修改项 |
|------|--------|
| `import_apkg.py` 或新脚本 | DECK 名、apkg 路径 |
| `parse_grammar.py` | 源 md 路径、输出 JSON 路径 |
| `create_grammar_deck.py` | DECK 名 |
| `fill_minna_examples.py` | DECK 名、examples 路径 |
| `tts_minna_examples.py` | DECK 名 |
| `config.py` | `VOCAB_DECKS` / `GRAMMAR_DECK` 列表 |
| `unlock.py` | DECK 名 |

### Step 3: 执行流程

```bash
# 単語导入
python3 anki/sync.py           # 或自定义导入脚本

# 文法制作
python3 anki/parse_grammar.py
python3 anki/generate_grammar_quiz.py
# ... 编辑 quiz JSON ...
python3 anki/create_grammar_deck.py

# 例句 + TTS
python3 anki/generate_examples.py
python3 anki/fill_minna_examples.py
python3 anki/tts_minna_examples.py

# 配置 SRS
python3 anki/config.py
```

## 文件结构

```
anki/
├── import_apkg.py            # 単語首次导入（blank.apkg → Anki）
├── sync.py                   # 双 Profile 同步导入
├── add.py                    # 补充新单词（補充単語）
├── unlock.py                 # 解锁中文→日文卡片
├── config.py                 # SRS 复习策略配置
├── update_theme.py           # 更新卡片 CSS 样式
│
├── fill_minna_examples.py    # 从 JSON 填充例句到卡片
├── generate_examples.py      # 按词性模板生成例句 JSON
├── tts_minna_examples.py     # 例句 TTS（WhiteCUL 楽しい）
├── tts.py                    # 补充単語 TTS（琴詠ニア）
│
├── parse_grammar.py          # 文法.md → grammar_data.json
├── generate_grammar_quiz.py  # 选择题模板生成 + 完整性检查
├── create_grammar_deck.py    # 文法卡包创建 + 导入
│
├── examples/                 # 每课例句 JSON
│   ├── lesson_01.json
│   ├── ...
│   └── lesson_50.json
│
├── grammar/                  # 文法数据
│   ├── grammar_data.json     # 139 语法点（解析自文法.md）
│   └── grammar_quiz.json     # 选择题数据
│
├── blank.apkg                # 源数据（2387 词 + 2263 音频）
├── legacy/                   # 旧版脚本存档
└── README.md
```

## 技术要点

- **AnkiConnect API**：所有操作通过 `localhost:8765` HTTP API 完成
- **Profile 切换**：`loadProfile` 是异步的，切换后必须 `sleep(10)` + sanity check
- **Furigana**：`strip_furigana` 先删 `[reading]` 再删空格，不能用贪婪匹配
- **例句音频**：字段存纯文件名（不带 `[sound:]`），模板 JS 点击播放
- **V3 调度器**：config 需同时写 `new.delays`/`new.ints` 和 `new.learningSteps`/`new.graduatingIvl`
- **iOS 触控**：🔊 按钮采用 44px touch target（Apple 推荐最小值）
