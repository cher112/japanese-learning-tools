#!/usr/bin/env python3
"""
从 blank.apkg 提取数据，用 Duolingo 风格导入 Anki
- 2387 notes, 2263 audio files, 50 lessons
- 三向卡片: 假名→日文+中文, 日文→读音+中文, 中文→日文
"""
import json
import sqlite3
import urllib.request
import zipfile
import os
import sys
import time
import base64

# Bypass proxy for localhost
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"

# Use a no-proxy handler
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

APKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blank.apkg")
ANKI_URL = "http://localhost:8765"
DECK_PREFIX = "初级1-2"
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


# ─── CSS ───
CSS = r"""
/* ===== Duolingo × みんなの日本語 ===== */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&family=Noto+Sans+JP:wght@400;700;900&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body { background: #235390; min-height: 100vh; }

.card {
  font-family: 'Nunito', 'Noto Sans JP', 'Hiragino Sans', system-ui, sans-serif;
  background: #235390;
  color: #4b4b4b;
  max-width: 480px;
  margin: 0 auto;
  padding: 28px 16px;
  text-align: center;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* === 主卡片 === */
.card-box {
  background: #fff;
  border-radius: 16px;
  padding: 36px 28px 28px;
  box-shadow: 0 4px 0 #1a4373;
  animation: popIn 0.25s ease-out;
}
@keyframes popIn {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* === 卡片类型标签 === */
.card-type {
  display: inline-block;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  padding: 4px 16px;
  border-radius: 20px;
  margin-bottom: 20px;
}
.card-type.kana    { background: #e5e5e5; color: #777; }
.card-type.kanji   { background: #ddf4ff; color: #1cb0f6; }
.card-type.chinese { background: #fff4e0; color: #ff9600; }

/* === 日语主词 === */
.word {
  font-size: 48px;
  font-weight: 900;
  color: #3c3c3c;
  margin: 8px 0;
  letter-spacing: 2px;
  line-height: 1.3;
}

/* === 假名读音 === */
.reading {
  font-size: 22px;
  font-weight: 800;
  color: #1cb0f6;
  margin: 4px 0 6px;
  letter-spacing: 1px;
}

/* === 音调标记 === */
.pitch {
  font-size: 16px;
  font-weight: 800;
  color: #1cb0f6;
  margin-left: 4px;
  vertical-align: super;
}

/* === 词性胶囊 === */
.pos-tag {
  display: inline-block;
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  background: #58cc02;
  padding: 5px 18px;
  border-radius: 20px;
  box-shadow: 0 3px 0 #43c000;
  margin: 8px 4px;
  letter-spacing: 0.5px;
}

/* === 基本形标签 === */
.dict-form {
  font-size: 15px;
  font-weight: 700;
  color: #afafaf;
  margin: 6px 0;
}

/* === 外来语标签 === */
.loanword {
  display: inline-block;
  font-size: 12px;
  font-weight: 800;
  color: #afafaf;
  background: #f7f7f7;
  border: 2px solid #e5e5e5;
  padding: 3px 12px;
  border-radius: 16px;
  margin: 6px 0;
}

/* === 释义区 === */
.meaning-block {
  text-align: left;
  margin: 18px 0 0;
  padding: 16px 20px;
  background: #f7f7f7;
  border-radius: 14px;
  border: 2px solid #e5e5e5;
  box-shadow: 0 2px 0 #e5e5e5;
}
.meaning-title {
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: #ff9600;
  margin-bottom: 6px;
}
.meaning-text {
  font-size: 20px;
  color: #3c3c3c;
  font-weight: 800;
  line-height: 1.7;
}

/* === 中文大字（正面） === */
.meaning-front {
  font-size: 36px;
  font-weight: 900;
  color: #3c3c3c;
  margin: 8px 0;
  line-height: 1.4;
}

/* === 例句区 === */
.example-block {
  text-align: left;
  margin: 12px 0 0;
  padding: 14px 20px;
  background: #f7f7f7;
  border-radius: 14px;
  border: 2px solid #e5e5e5;
  border-left: 4px solid #58cc02;
}
.example-title {
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: #58cc02;
  margin-bottom: 4px;
}
.example-jp {
  font-size: 16px;
  color: #3c3c3c;
  font-weight: 700;
  line-height: 1.8;
}

/* === 分隔线 === */
.divider { height: 2px; background: #e5e5e5; margin: 18px 0; border: none; border-radius: 1px; }

/* === 音频按钮 === */
.audio-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px; height: 44px;
  background: #1cb0f6;
  border-radius: 50%;
  box-shadow: 0 3px 0 #0899d6;
  cursor: pointer;
  margin: 8px 0;
  transition: transform 0.1s;
}
.audio-btn:active { transform: scale(0.95); }
.audio-btn svg { fill: #fff; width: 20px; height: 20px; }

/* === Furigana ruby === */
ruby { ruby-align: center; }
ruby rt { font-size: 0.55em; font-weight: 700; color: #1cb0f6; }

/* === 夜间模式 → 强制浅色 === */
.nightMode, .nightMode .card, .nightMode html, .nightMode body { background: #235390 !important; }
.nightMode .card-box { background: #fff !important; }
.nightMode .word, .nightMode .meaning-text, .nightMode .example-jp, .nightMode .meaning-front { color: #3c3c3c !important; }
.nightMode .reading, .nightMode .pitch { color: #1cb0f6 !important; }
.nightMode .meaning-block, .nightMode .example-block { background: #f7f7f7 !important; border-color: #e5e5e5 !important; }
.nightMode .pos-tag { background: #58cc02 !important; color: #fff !important; }
"""

# Audio play icon SVG
AUDIO_SVG = '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>'

# ─── Templates ───

# 卡片1: 假名→日文+中文 (only for kanji words)
FRONT_KANA = """
{{#是否需要从汉字到假名}}
<div class="card-box">
  <div class="card-type kana">假名 → 日文</div>
  <div class="word">{{kana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{kana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{#音频}}<div class="audio-btn" onclick="var a=document.getElementById('au');if(a){a.play();}">""" + AUDIO_SVG + """</div>{{/音频}}
  {{#音频}}<div style="display:none">{{音频}}</div>{{/音频}}
</div>
{{/是否需要从汉字到假名}}
"""

BACK_KANA = """
{{#是否需要从汉字到假名}}
<div class="card-box">
  <div class="card-type kana">假名 → 日文</div>
  <div class="word">{{furigana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{furigana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
  {{#音频}}<div class="audio-btn" onclick="var a=document.getElementById('au');if(a){a.play();}">""" + AUDIO_SVG + """</div>{{/音频}}
  {{#音频}}<div style="display:none">{{音频}}</div>{{/音频}}

  <div class="meaning-block">
    <div class="meaning-title">释义</div>
    <div class="meaning-text">{{中文}}</div>
  </div>

  {{#外来语}}<div class="loanword">{{外来语}}</div>{{/外来语}}

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句</div>
    <div class="example-jp">{{例句}}</div>
  </div>
  {{/例句}}
</div>
{{/是否需要从汉字到假名}}
"""

# 卡片2: 日文→读音+中文
FRONT_JP = """
<div class="card-box">
  <div class="card-type kanji">日文 → 含义</div>
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
  <div class="card-type kanji">日文 → 含义</div>
  <div class="word">{{furigana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{furigana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
  {{#音频}}<div class="audio-btn" onclick="var a=document.getElementById('au');if(a){a.play();}">""" + AUDIO_SVG + """</div>{{/音频}}
  {{#音频}}<div style="display:none">{{音频}}</div>{{/音频}}

  <div class="meaning-block">
    <div class="meaning-title">释义</div>
    <div class="meaning-text">{{中文}}</div>
  </div>

  {{#外来语}}<div class="loanword">{{外来语}}</div>{{/外来语}}

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句</div>
    <div class="example-jp">{{例句}}</div>
  </div>
  {{/例句}}
</div>
"""

# 卡片3: 中文→日文
FRONT_CN = """
<div class="card-box">
  <div class="card-type chinese">中文 → 日文</div>
  <div class="meaning-front">{{中文}}</div>
</div>
"""

BACK_CN = """
<div class="card-box">
  <div class="card-type chinese">中文 → 日文</div>
  <div class="word">{{furigana:日文}}</div>
  {{#基本形}}<div class="dict-form">（←{{furigana:基本形}}<span class="pitch">{{音调核}}</span>）</div>{{/基本形}}
  {{^基本形}}{{#音调核}}<div class="reading"><span class="pitch">{{音调核}}</span></div>{{/音调核}}{{/基本形}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
  {{#音频}}<div class="audio-btn" onclick="var a=document.getElementById('au');if(a){a.play();}">""" + AUDIO_SVG + """</div>{{/音频}}
  {{#音频}}<div style="display:none">{{音频}}</div>{{/音频}}

  {{#外来语}}<div class="loanword">{{外来语}}</div>{{/外来语}}

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句</div>
    <div class="example-jp">{{例句}}</div>
  </div>
  {{/例句}}
</div>
"""


def extract_apkg():
    """Extract notes, decks, and media from blank.apkg"""
    zf = zipfile.ZipFile(APKG, "r")

    # Read media mapping
    media_map = json.loads(zf.read("media"))

    # Read SQLite
    import tempfile
    tmp = tempfile.mktemp(suffix=".db")
    with open(tmp, "wb") as f:
        f.write(zf.read("collection.anki21"))

    db = sqlite3.connect(tmp)
    col_data = db.execute("SELECT models, decks FROM col").fetchone()
    models = json.loads(col_data[0])
    decks_raw = json.loads(col_data[1])

    # Build deck_id -> lesson name mapping
    deck_map = {}
    for did, d in decks_raw.items():
        name = d["name"]
        # Extract lesson number: "みんなの日本語　初級::第０１課　単語" -> "第01課"
        if "::第" in name:
            part = name.split("::")[1]  # "第０１課　単語"
            # Normalize fullwidth digits
            lesson = part.split("　")[0]  # "第０１課"
            lesson = lesson.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            deck_map[int(did)] = lesson
        else:
            deck_map[int(did)] = ""

    # Get field names from model
    model = list(models.values())[0]
    field_names = [f["name"] for f in model["flds"]]

    # Read all notes
    notes = db.execute("SELECT id, flds FROM notes").fetchall()

    # Build note_id -> deck mapping via cards table
    note_decks = {}
    cards = db.execute("SELECT nid, did FROM cards").fetchall()
    for nid, did in cards:
        if nid not in note_decks:
            note_decks[nid] = did

    # Parse notes
    parsed = []
    for nid, flds in notes:
        fields = flds.split("\x1f")
        note = {}
        for i, name in enumerate(field_names):
            note[name] = fields[i] if i < len(fields) else ""
        note["_lesson"] = deck_map.get(note_decks.get(nid, 0), "")
        parsed.append(note)

    db.close()
    os.unlink(tmp)

    return parsed, media_map, zf


def main():
    print("=" * 55)
    print("  blank.apkg → Anki (Duolingo Style)")
    print("=" * 55)

    # 1. Extract data
    print("\n📦 解压 apkg...")
    notes, media_map, zf = extract_apkg()
    print(f"  ✓ {len(notes)} 个单词, {len(media_map)} 个音频")

    # 2. Connect to Anki
    try:
        anki("version")
        print("  ✓ AnkiConnect 连接成功")
    except Exception:
        print("  ✗ 请打开 Anki 并确认 AnkiConnect 已安装")
        return

    # 3. Delete old deck
    print("\n🗑  清理旧牌组...")
    try:
        anki("deleteDecks", decks=[DECK_PREFIX], cardsToo=True)
        print(f"  ✓ 已删除「{DECK_PREFIX}」")
    except Exception:
        print(f"  - 「{DECK_PREFIX}」不存在，跳过")

    # Also try to delete sub-decks
    try:
        deck_names = anki("deckNames")
        for d in deck_names:
            if d.startswith(DECK_PREFIX + "::"):
                anki("deleteDecks", decks=[d], cardsToo=True)
    except Exception:
        pass

    # 4. Create model
    print("\n📐 创建模型和模板...")
    try:
        existing = anki("modelNames")
        if MODEL in existing:
            # Delete and recreate
            pass  # We'll update instead

        if MODEL not in existing:
            anki("createModel",
                 modelName=MODEL,
                 inOrderFields=["日文", "音调核", "词性", "基本形", "外来语",
                                "中文", "音频", "是否需要从汉字到假名",
                                "是否需要缩小日文", "是否需要缩小假名",
                                "是否需要缩小中文", "例句"],
                 css=CSS,
                 cardTemplates=[
                     {"Name": "假名", "Front": FRONT_KANA, "Back": BACK_KANA},
                     {"Name": "日文", "Front": FRONT_JP, "Back": BACK_JP},
                     {"Name": "中文", "Front": FRONT_CN, "Back": BACK_CN},
                 ])
            print(f"  ✓ 模型「{MODEL}」已创建")
        else:
            # Update existing model
            anki("updateModelStyling", model={"name": MODEL, "css": CSS})
            anki("updateModelTemplates", model={
                "name": MODEL,
                "templates": {
                    "假名": {"Front": FRONT_KANA, "Back": BACK_KANA},
                    "日文": {"Front": FRONT_JP, "Back": BACK_JP},
                    "中文": {"Front": FRONT_CN, "Back": BACK_CN},
                }
            })
            # Ensure 例句 field exists
            fields = anki("modelFieldNames", modelName=MODEL)
            if "例句" not in fields:
                anki("modelFieldAdd", modelName=MODEL, fieldName="例句", index=len(fields))
            print(f"  ✓ 模型「{MODEL}」已更新")
    except Exception as e:
        print(f"  ✗ 模型创建失败: {e}")
        return

    # 5. Create sub-decks
    print("\n📚 创建子牌组...")
    lessons = sorted(set(n["_lesson"] for n in notes if n["_lesson"]))
    for lesson in lessons:
        deck_name = f"{DECK_PREFIX}::{lesson}"
        anki("createDeck", deck=deck_name)
    print(f"  ✓ {len(lessons)} 个子牌组")

    # 6. Upload media files
    print("\n🔊 上传音频文件...")
    uploaded = 0
    for num_str, filename in media_map.items():
        try:
            data = zf.read(num_str)
            b64 = base64.b64encode(data).decode("utf-8")
            anki("storeMediaFile", filename=filename, data=b64)
            uploaded += 1
            if uploaded % 100 == 0:
                sys.stdout.write(f"\r  [{uploaded}/{len(media_map)}]...")
                sys.stdout.flush()
        except Exception:
            pass
    print(f"\r  ✓ {uploaded} 个媒体文件已上传")

    # 7. Import notes
    print("\n📝 导入卡片...")
    added = 0
    skipped = 0
    for i, note in enumerate(notes):
        lesson = note["_lesson"]
        deck_name = f"{DECK_PREFIX}::{lesson}" if lesson else DECK_PREFIX

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

        if (i + 1) % 50 == 0:
            sys.stdout.write(f"\r  [{i+1}/{len(notes)}] 已添加 {added}...")
            sys.stdout.flush()

    print(f"\r  ✓ 导入完成: {added} 张新卡片, {skipped} 张跳过")

    # 8. Summary
    print(f"\n{'=' * 55}")
    print(f"  ✅ 完成！")
    print(f"  牌组: {DECK_PREFIX}")
    print(f"  单词: {added}")
    print(f"  音频: {uploaded}")
    print(f"  课程: {len(lessons)}")
    print(f"  模板: 假名/日文/中文 三向卡片")
    print(f"{'=' * 55}")

    zf.close()


if __name__ == "__main__":
    main()
