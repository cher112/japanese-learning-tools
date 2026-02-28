#!/usr/bin/env python3
"""
从 blank.apkg 导入 Anki — Duolingo 风格，双向卡片
  卡片1: 日文→含义（主力）
  卡片2: 中文→日文（默认挂起，用 unlock.py 解锁）
"""
import json
import sqlite3
import urllib.request
import zipfile
import os
import sys
import base64
import tempfile

# Bypass proxy for localhost
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

APKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blank.apkg")
ANKI_URL = "http://localhost:8765"
DECK = "みんなの日本語初级1-2 単語"
MODEL = "みんなの日本語"


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


# ─── CSS ─────────────────────────────────────────────
CSS = r"""
/* ===== Duolingo Soft Blue × みんなの日本語 ===== */
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800;900&family=Noto+Sans+JP:wght@400;700;900&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #5b9bd5; min-height: 100vh; }

.card {
  font-family: 'Nunito Sans', 'Noto Sans JP', 'Hiragino Sans', system-ui, sans-serif;
  background: #5b9bd5;
  color: #4b4b4b;
  max-width: 440px;
  margin: 0 auto;
  padding: 24px 14px;
  text-align: center;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* === 主卡片 === */
.card-box {
  background: #fff;
  border-radius: 24px;
  padding: 32px 26px 26px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.10), 0 3px 0 #4080b8;
  animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes popIn {
  from { opacity: 0; transform: translateY(16px) scale(0.95); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* === 顶部栏：类型 + 课号 === */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.card-type {
  display: inline-block;
  font-size: 11px; font-weight: 800;
  letter-spacing: 1px;
  padding: 5px 14px; border-radius: 20px;
}
.card-type.kanji   { background: #eef6ff; color: #5b9bf6; }
.card-type.chinese { background: #fff5eb; color: #f5a623; }

.lesson-tag {
  font-size: 11px; font-weight: 800;
  color: #b0b0b0; background: #f4f4f5;
  padding: 5px 12px; border-radius: 20px;
  letter-spacing: 0.5px;
}

/* === 日语主词 === */
.word {
  font-size: 46px; font-weight: 900; color: #2d2d2d;
  margin: 6px 0; letter-spacing: 2px; line-height: 1.35;
}

/* === 假名读音 === */
.reading {
  font-size: 20px; font-weight: 700; color: #5b9bf6;
  margin: 4px 0 6px; letter-spacing: 1px;
}

/* === 音调标记 === */
.pitch {
  font-size: 14px; font-weight: 800; color: #5b9bf6;
  margin-left: 3px; vertical-align: super;
}

/* === 词性胶囊 === */
.pos-tag {
  display: inline-block; font-size: 12px; font-weight: 800;
  color: #fff; background: #58cc02;
  padding: 5px 16px; border-radius: 20px;
  box-shadow: 0 2px 0 #4ab800;
  margin: 8px 4px;
}

/* === 基本形 === */
.dict-form {
  font-size: 14px; font-weight: 700; color: #b8b8b8; margin: 6px 0;
}

/* === 外来语 === */
.loanword {
  display: inline-block; font-size: 11px; font-weight: 700;
  color: #b0b0b0; background: #f8f8f8;
  border: 1.5px solid #ececec;
  padding: 3px 12px; border-radius: 14px; margin: 6px 0;
}

/* === 释义区 === */
.meaning-block {
  text-align: left; margin: 16px 0 0; padding: 16px 18px;
  background: #fafafa; border-radius: 16px;
  border: 1.5px solid #eeeeee;
}
.meaning-title {
  font-size: 11px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1px; color: #f5a623; margin-bottom: 6px;
}
.meaning-text {
  font-size: 19px; color: #2d2d2d; font-weight: 700; line-height: 1.7;
}

/* === 中文正面大字 === */
.meaning-front {
  font-size: 34px; font-weight: 900; color: #2d2d2d;
  margin: 8px 0; line-height: 1.4;
}

/* === 例句区 === */
.example-block {
  text-align: left; margin: 10px 0 0; padding: 14px 18px;
  background: #f0faf0; border-radius: 16px;
  border: 1.5px solid #d5f0d5;
}
.example-title {
  font-size: 11px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1px; color: #58cc02; margin-bottom: 4px;
}
.example-jp {
  font-size: 15px; color: #2d2d2d; font-weight: 600; line-height: 1.8;
}
.example-cn {
  font-size: 12px; color: #888; margin-top: 2px;
}

/* === Furigana === */
ruby { ruby-align: center; }
ruby rt { font-size: 0.55em; font-weight: 700; color: #5b9bf6; }

/* === nightMode === */
.nightMode, .nightMode .card, .nightMode html, .nightMode body { background: #5b9bd5 !important; }
.nightMode .card-box { background: #fff !important; }
.nightMode .word, .nightMode .meaning-text, .nightMode .example-jp, .nightMode .meaning-front { color: #2d2d2d !important; }
.nightMode .reading, .nightMode .pitch, .nightMode ruby rt { color: #5b9bf6 !important; }
.nightMode .meaning-block { background: #fafafa !important; border-color: #eee !important; }
.nightMode .example-block { background: #f0faf0 !important; border-color: #d5f0d5 !important; }
.nightMode .pos-tag { background: #58cc02 !important; color: #fff !important; }

/* === 音频：多邻国风格播放按钮 === */
.replay-button {
  display: inline-flex !important; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 12px;
  background: linear-gradient(135deg, #78d9ff 0%, #5b9bf6 100%);
  border: none; box-shadow: 0 3px 0 #4080c0;
  vertical-align: middle; margin: 2px 4px;
  cursor: pointer; transition: all 0.12s;
}
.replay-button:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #4080c0;
}
.replay-button svg { display: none !important; }
.replay-button::after {
  content: "\1F50A"; font-size: 18px; line-height: 1;
}
/* 例句区内：纯 emoji，无背景 */
.example-block .replay-button { display: none !important; }
.ex-play-btn {
  cursor: pointer; font-size: 20px; vertical-align: middle;
  margin-left: 4px; user-select: none; -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
  /* 扩大触摸区域：44px是Apple推荐最小触摸尺寸 */
  display: inline-flex; align-items: center; justify-content: center;
  width: 44px; height: 44px;
  margin: -10px -10px -10px 0;
  position: relative;
  border-radius: 50%;
}
.ex-play-btn:active { transform: scale(1.3); background: rgba(91,155,246,0.1); }

/* === 已记住按钮（仅桌面） === */
.master-wrap { margin: 16px 0 0; text-align: center; display: none; }
.master-btn {
  font-family: 'Nunito Sans', 'Noto Sans JP', system-ui, sans-serif;
  font-size: 13px; font-weight: 800;
  color: #fff; background: #f5a623;
  border: none; border-radius: 20px;
  padding: 9px 24px;
  box-shadow: 0 3px 0 #d4891a;
  cursor: pointer; letter-spacing: 1px;
  transition: all 0.15s;
}
.master-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #d4891a;
}
.master-btn.done {
  background: #b0b0b0; box-shadow: 0 1px 0 #999;
  pointer-events: none;
}
"""

# ─── Templates ────────────────────────────────────────

# 卡片1: 日文→含义（主力卡片）
FRONT_JP = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type kanji">日文 → 含义</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  {{#是否需要从汉字到假名}}
  <div class="word">{{kanji:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{kanji:基本形}}）</div>{{/基本形}}
  {{/是否需要从汉字到假名}}
  {{^是否需要从汉字到假名}}
  <div class="word">{{furigana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{kana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{/是否需要从汉字到假名}}
</div>
"""

BACK_JP = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type kanji">日文 → 含义</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="word">{{furigana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{furigana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
  {{#音频}}{{音频}}{{/音频}}

  <div class="meaning-block">
    <div class="meaning-title">释义</div>
    <div class="meaning-text">{{中文}}</div>
  </div>

  {{#外来语}}<div class="loanword">{{外来语}}</div>{{/外来语}}

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句 {{#例句音频}}<span class="ex-play-btn" onclick="playEx(this)" data-f="{{例句音频}}">🔊</span>{{/例句音频}}</div>
    <div class="example-jp">{{例句}}</div>
    {{#例句翻译}}<div class="example-cn">{{例句翻译}}</div>{{/例句翻译}}
  </div>
  {{/例句}}

  <div class="master-wrap">
    <button class="master-btn" onclick="markMastered(this)">已记住</button>
  </div>
</div>
<script>
function playEx(el) {
  var f = el.getAttribute('data-f');
  if (f) { var a = new Audio(f); a.play(); }
}
function markMastered(btn) {
  var api = 'http://127.0.0.1:8765';
  function post(action, params) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', api, false);
    xhr.send(JSON.stringify({action:action,version:6,params:params||{}}));
    return JSON.parse(xhr.responseText);
  }
  try {
    var d = post('guiCurrentCard');
    if (!d.result) return;
    var nid = d.result.noteId;
    var d2 = post('findCards', {query:'nid:'+nid});
    if (d2.result) {
      post('suspend', {cards:d2.result});
      post('addTags', {notes:[nid], tags:'mastered'});
    }
    btn.textContent = '\u2713 \u5df2\u8bb0\u4f4f';
    btn.className = 'master-btn done';
    setTimeout(function(){ post('guiAnswerCard', {ease:3}); }, 300);
  } catch(e) {}
}
(function(){
  try {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:8765', false);
    xhr.send(JSON.stringify({action:'version',version:6}));
    var wraps = document.querySelectorAll('.master-wrap');
    for (var i = 0; i < wraps.length; i++) wraps[i].style.display = 'block';
  } catch(e) {}
})();
</script>
"""

# 卡片2: 中文→日文（默认挂起）
FRONT_CN = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type chinese">中文 → 日文</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="meaning-front">{{中文}}</div>
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
</div>
"""

BACK_CN = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type chinese">中文 → 日文</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="word">{{furigana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{furigana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
  {{#音频}}{{音频}}{{/音频}}

  {{#外来语}}<div class="loanword">{{外来语}}</div>{{/外来语}}

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句 {{#例句音频}}<span class="ex-play-btn" onclick="playEx(this)" data-f="{{例句音频}}">🔊</span>{{/例句音频}}</div>
    <div class="example-jp">{{例句}}</div>
    {{#例句翻译}}<div class="example-cn">{{例句翻译}}</div>{{/例句翻译}}
  </div>
  {{/例句}}

  <div class="master-wrap">
    <button class="master-btn" onclick="markMastered(this)">已记住</button>
  </div>
</div>
<script>
function playEx(el) {
  var f = el.getAttribute('data-f');
  if (f) { var a = new Audio(f); a.play(); }
}
function markMastered(btn) {
  var api = 'http://127.0.0.1:8765';
  function post(action, params) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', api, false);
    xhr.send(JSON.stringify({action:action,version:6,params:params||{}}));
    return JSON.parse(xhr.responseText);
  }
  try {
    var d = post('guiCurrentCard');
    if (!d.result) return;
    var nid = d.result.noteId;
    var d2 = post('findCards', {query:'nid:'+nid});
    if (d2.result) {
      post('suspend', {cards:d2.result});
      post('addTags', {notes:[nid], tags:'mastered'});
    }
    btn.textContent = '\u2713 \u5df2\u8bb0\u4f4f';
    btn.className = 'master-btn done';
    setTimeout(function(){ post('guiAnswerCard', {ease:3}); }, 300);
  } catch(e) {}
}
(function(){
  try {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:8765', false);
    xhr.send(JSON.stringify({action:'version',version:6}));
    var wraps = document.querySelectorAll('.master-wrap');
    for (var i = 0; i < wraps.length; i++) wraps[i].style.display = 'block';
  } catch(e) {}
})();
</script>
"""


def extract_apkg():
    """Extract notes, decks, and media from blank.apkg"""
    zf = zipfile.ZipFile(APKG, "r")
    media_map = json.loads(zf.read("media"))

    tmp = tempfile.mktemp(suffix=".db")
    with open(tmp, "wb") as f:
        f.write(zf.read("collection.anki21"))

    db = sqlite3.connect(tmp)
    col_data = db.execute("SELECT models, decks FROM col").fetchone()
    models = json.loads(col_data[0])
    decks_raw = json.loads(col_data[1])

    # deck_id -> lesson name
    deck_map = {}
    for did, d in decks_raw.items():
        name = d["name"]
        if "::第" in name:
            part = name.split("::")[1]
            lesson = part.split("\u3000")[0]  # fullwidth space
            lesson = lesson.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            deck_map[int(did)] = lesson
        else:
            deck_map[int(did)] = ""

    model = list(models.values())[0]
    field_names = [f["name"] for f in model["flds"]]

    notes = db.execute("SELECT id, flds FROM notes").fetchall()
    note_decks = {}
    for nid, did in db.execute("SELECT nid, did FROM cards"):
        if nid not in note_decks:
            note_decks[nid] = did

    parsed = []
    for nid, flds in notes:
        fields = flds.split("\x1f")
        note = {name: (fields[i] if i < len(fields) else "") for i, name in enumerate(field_names)}
        note["_lesson"] = deck_map.get(note_decks.get(nid, 0), "")
        parsed.append(note)

    db.close()
    os.unlink(tmp)
    return parsed, media_map, zf


def main():
    print("=" * 55)
    print("  blank.apkg → Anki (Duolingo Style)")
    print("  2 卡片: 日文→含义 + 中文→日文(挂起)")
    print("=" * 55)

    # 1. Extract
    print("\n[1/6] 解压 apkg...")
    notes, media_map, zf = extract_apkg()
    print(f"  {len(notes)} 个单词, {len(media_map)} 个音频")

    # 2. Connect
    try:
        anki("version")
        print("  AnkiConnect OK")
    except Exception:
        print("  ✗ 请打开 Anki")
        return

    # 3. Clean old data
    print("\n[2/6] 清理旧数据...")
    try:
        deck_names = anki("deckNames")
        to_delete = [d for d in deck_names if d == DECK or d.startswith(DECK + "::")]
        if to_delete:
            anki("deleteDecks", decks=to_delete, cardsToo=True)
            print(f"  已删除 {len(to_delete)} 个牌组")
    except Exception:
        pass

    # Also clean old model if exists (to recreate fresh)
    try:
        existing_models = anki("modelNames")
        if MODEL in existing_models:
            # Check if model has notes - if deck deleted, notes gone, safe to proceed
            # We'll just recreate below; if model exists with no notes, createModel will fail
            # so we update instead
            pass
    except Exception:
        pass

    # 4. Create model
    print("\n[3/6] 创建模型...")
    try:
        existing = anki("modelNames")
        if MODEL not in existing:
            anki("createModel",
                 modelName=MODEL,
                 inOrderFields=["日文", "音调核", "词性", "基本形", "外来语",
                                "中文", "音频", "是否需要从汉字到假名",
                                "是否需要缩小日文", "是否需要缩小假名",
                                "是否需要缩小中文", "例句", "課", "例句音频"],
                 css=CSS,
                 cardTemplates=[
                     {"Name": "日文", "Front": FRONT_JP, "Back": BACK_JP},
                     {"Name": "中文", "Front": FRONT_CN, "Back": BACK_CN},
                 ])
            print(f"  模型「{MODEL}」已创建 (2 模板)")
        else:
            # Add new fields first (before templates reference them)
            fields = anki("modelFieldNames", modelName=MODEL)
            if "例句" not in fields:
                anki("modelFieldAdd", modelName=MODEL, fieldName="例句", index=len(fields))
            fields = anki("modelFieldNames", modelName=MODEL)
            if "課" not in fields:
                anki("modelFieldAdd", modelName=MODEL, fieldName="課", index=len(fields))
            fields = anki("modelFieldNames", modelName=MODEL)
            if "例句音频" not in fields:
                anki("modelFieldAdd", modelName=MODEL, fieldName="例句音频", index=len(fields))
            # Now update styling and templates
            anki("updateModelStyling", model={"name": MODEL, "css": CSS})
            anki("updateModelTemplates", model={
                "name": MODEL,
                "templates": {
                    "日文": {"Front": FRONT_JP, "Back": BACK_JP},
                    "中文": {"Front": FRONT_CN, "Back": BACK_CN},
                }
            })
            print(f"  模型「{MODEL}」已更新")
    except Exception as e:
        print(f"  ✗ 模型失败: {e}")
        return

    # 5. Create sub-decks
    lessons = sorted(set(n["_lesson"] for n in notes if n["_lesson"]))
    for lesson in lessons:
        anki("createDeck", deck=f"{DECK}::{lesson}")

    # 6. Upload media
    print(f"\n[4/6] 上传 {len(media_map)} 个音频...")
    uploaded = 0
    for num_str, filename in media_map.items():
        try:
            data = zf.read(num_str)
            b64 = base64.b64encode(data).decode("utf-8")
            anki("storeMediaFile", filename=filename, data=b64)
            uploaded += 1
            if uploaded % 200 == 0:
                sys.stdout.write(f"\r  [{uploaded}/{len(media_map)}]")
                sys.stdout.flush()
        except Exception:
            pass
    print(f"\r  {uploaded} 个媒体文件已上传")

    # 7. Import notes
    print(f"\n[5/6] 导入 {len(notes)} 个单词...")
    added = 0
    skipped = 0
    for i, note in enumerate(notes):
        lesson = note["_lesson"]
        deck_name = f"{DECK}::{lesson}" if lesson else DECK
        try:
            ids = anki("addNotes", notes=[{
                "deckName": deck_name,
                "modelName": MODEL,
                "fields": {
                    "日文": note["日文"],
                    "音调核": note["音调核"],
                    "词性": note["词性"],
                    "基本形": note["基本形"],
                    "外来语": note["外来语"],
                    "中文": note["中文"],
                    "音频": note["音频"],
                    "是否需要从汉字到假名": note["是否需要从汉字到假名"],
                    "是否需要缩小日文": note.get("是否需要缩小日文", ""),
                    "是否需要缩小假名": note.get("是否需要缩小假名", ""),
                    "是否需要缩小中文": note.get("是否需要缩小中文", ""),
                    "例句": "",
                    "課": note["_lesson"],
                    "例句音频": "",
                },
                "options": {"allowDuplicate": False},
                "tags": [lesson, note["词性"]] if lesson else [note["词性"]],
            }])
            if ids and ids[0]:
                added += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1
        if (i + 1) % 100 == 0:
            sys.stdout.write(f"\r  [{i+1}/{len(notes)}] +{added}")
            sys.stdout.flush()
    print(f"\r  {added} 张新卡片, {skipped} 张跳过")

    # 8. Suspend all 中文→日文 cards (ord=1, 0-indexed)
    print(f"\n[6/6] 挂起「中文→日文」卡片...")
    try:
        # Find all cards for this deck, then filter by template ord
        card_ids = anki("findCards", query=f'"deck:{DECK}" card:2')
        if card_ids:
            anki("suspend", cards=card_ids)
            print(f"  {len(card_ids)} 张「中文→日文」卡片已挂起")
            print(f"  用 unlock.py 解锁已熟悉的词")
        else:
            print("  未找到需要挂起的卡片")
    except Exception as e:
        print(f"  挂起失败: {e}")

    # Summary
    print(f"\n{'=' * 55}")
    print(f"  ✅ 导入完成！")
    print(f"  牌组: {DECK} ({len(lessons)} 课)")
    print(f"  单词: {added}  音频: {uploaded}")
    print(f"  日文→含义: 正常学习")
    print(f"  中文→日文: 已挂起 (run unlock.py)")
    print(f"{'=' * 55}")
    zf.close()


if __name__ == "__main__":
    main()
