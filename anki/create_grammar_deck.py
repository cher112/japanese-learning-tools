#!/usr/bin/env python3
"""
文法 Anki 卡包 — 語法認識 + 多邻国风選択問題
  Model 1: 文法認識 — 正面：句型 + 代表例句，背面：中文说明 + 全部例句
  Model 2: 文法選択 — 多邻国风 4 选 1 选择题
"""
import json
import urllib.request
import os
import sys
import time

# ─── Proxy bypass ──────────────────────────────────────
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# ─── Config ────────────────────────────────────────────
ANKI_URL = "http://localhost:8765"
PROFILES = ["szmz", "czh"]
DECK = "みんなの日本語初级1-2 文法"
MODEL_NINSHIKI = "文法認識"
MODEL_SENTAKU = "文法選択"

DIR = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_DATA = os.path.join(DIR, "grammar", "grammar_data.json")
GRAMMAR_QUIZ = os.path.join(DIR, "grammar", "grammar_quiz.json")


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


def wait_for_anki(timeout=30):
    for _ in range(timeout):
        try:
            anki("version")
            return True
        except Exception:
            time.sleep(1)
    return False


# ─── CSS ───────────────────────────────────────────────
CSS = r"""
/* ===== 文法カード — Duolingo Soft Blue ===== */
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

/* === 顶部栏 === */
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
.card-type.grammar { background: #eef6ff; color: #5b9bf6; }
.card-type.quiz    { background: #fff0f0; color: #ff6b6b; }

.lesson-tag {
  font-size: 11px; font-weight: 800;
  color: #b0b0b0; background: #f4f4f5;
  padding: 5px 12px; border-radius: 20px;
  letter-spacing: 0.5px;
}

/* === 句型名 === */
.grammar-title {
  font-size: 28px; font-weight: 900; color: #2d2d2d;
  margin: 8px 0 16px; letter-spacing: 1px; line-height: 1.4;
}

/* === 代表例句（正面） === */
.example-front {
  text-align: left; margin: 0; padding: 14px 18px;
  background: #f0faf0; border-radius: 16px;
  border: 1.5px solid #d5f0d5;
}
.example-front .ex-jp {
  font-size: 17px; color: #2d2d2d; font-weight: 600; line-height: 1.8;
}
.example-front .ex-cn {
  font-size: 13px; color: #888; margin-top: 2px;
}

/* === 说明区（背面） === */
.explain-block {
  text-align: left; margin: 16px 0 0; padding: 16px 18px;
  background: #fafafa; border-radius: 16px;
  border: 1.5px solid #eeeeee;
}
.explain-title {
  font-size: 11px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1px; color: #f5a623; margin-bottom: 6px;
}
.explain-text {
  font-size: 15px; color: #2d2d2d; font-weight: 600; line-height: 1.8;
  white-space: pre-wrap;
}

/* === 例句列表（背面） === */
.examples-block {
  text-align: left; margin: 10px 0 0; padding: 14px 18px;
  background: #f0faf0; border-radius: 16px;
  border: 1.5px solid #d5f0d5;
}
.examples-title {
  font-size: 11px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1px; color: #58cc02; margin-bottom: 4px;
}
.ex-item { margin-bottom: 8px; }
.ex-item .ex-jp {
  font-size: 15px; color: #2d2d2d; font-weight: 600; line-height: 1.8;
}
.ex-item .ex-cn {
  font-size: 12px; color: #888; margin-top: 1px;
}

/* ========== 選択問題 ========== */
.quiz-question {
  font-size: 22px; font-weight: 800; color: #2d2d2d;
  margin: 12px 0 20px; line-height: 1.5;
}
.quiz-question .blank {
  display: inline-block;
  min-width: 60px;
  border-bottom: 3px solid #5b9bf6;
  margin: 0 2px;
  color: transparent;
}

/* === 选项按钮 === */
.options {
  display: flex; flex-direction: column; gap: 10px;
  margin: 0 auto; max-width: 320px;
}
.opt-btn {
  display: block; width: 100%;
  font-family: 'Nunito Sans', 'Noto Sans JP', system-ui, sans-serif;
  font-size: 18px; font-weight: 700;
  color: #4b4b4b; background: #fff;
  border: 2.5px solid #e0e0e0;
  border-radius: 16px;
  padding: 14px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 2px 0 #d0d0d0;
}
.opt-btn:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 #d0d0d0;
}

/* 背面：正确答案 */
.opt-btn.correct {
  color: #fff !important;
  background: #58cc02 !important;
  border-color: #58cc02 !important;
  box-shadow: 0 3px 0 #4ab800 !important;
}
/* 背面：错误选项 */
.opt-btn.wrong {
  color: #bbb !important;
  background: #f8f8f8 !important;
  border-color: #eee !important;
  box-shadow: none !important;
}

/* === 解说区 === */
.hint-block {
  text-align: left; margin: 16px 0 0; padding: 14px 18px;
  background: #fff8e1; border-radius: 16px;
  border: 1.5px solid #ffe0a0;
}
.hint-title {
  font-size: 11px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1px; color: #f5a623; margin-bottom: 4px;
}
.hint-text {
  font-size: 14px; color: #2d2d2d; font-weight: 600; line-height: 1.7;
}

/* === nightMode === */
.nightMode, .nightMode .card, .nightMode html, .nightMode body { background: #5b9bd5 !important; }
.nightMode .card-box { background: #fff !important; }
.nightMode .grammar-title, .nightMode .quiz-question,
.nightMode .explain-text, .nightMode .ex-jp, .nightMode .hint-text { color: #2d2d2d !important; }
.nightMode .explain-block { background: #fafafa !important; border-color: #eee !important; }
.nightMode .examples-block, .nightMode .example-front { background: #f0faf0 !important; border-color: #d5f0d5 !important; }
.nightMode .hint-block { background: #fff8e1 !important; border-color: #ffe0a0 !important; }
.nightMode .opt-btn { background: #fff !important; color: #4b4b4b !important; }
.nightMode .opt-btn.correct { color: #fff !important; background: #58cc02 !important; }
.nightMode .opt-btn.wrong { color: #bbb !important; background: #f8f8f8 !important; }
"""

# ─── Model 1: 文法認識 Templates ────────────────────────
NINSHIKI_FRONT = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type grammar">語法認識</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="grammar-title" id="gtitle">{{正面}}</div>
  {{#代表例句}}
  <div class="example-front">
    {{代表例句}}
  </div>
  {{/代表例句}}
</div>
<script>
// Strip lesson prefix from display (e.g. "第1課 名詞1は..." → "名詞1は...")
(function(){
  var el = document.getElementById('gtitle');
  if (el) el.textContent = el.textContent.replace(/^第\\d+課\\s*/, '');
})();
</script>
"""

NINSHIKI_BACK = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type grammar">語法認識</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="grammar-title" id="gtitle2">{{正面}}</div>

  <div class="explain-block">
    <div class="explain-title">解説</div>
    <div class="explain-text">{{背面}}</div>
  </div>

  {{#例句一覧}}
  <div class="examples-block">
    <div class="examples-title">例句</div>
    {{例句一覧}}
  </div>
  {{/例句一覧}}
</div>
<script>
(function(){
  var el = document.getElementById('gtitle2');
  if (el) el.textContent = el.textContent.replace(/^第\\d+課\\s*/, '');
})();
</script>
"""

# ─── Model 2: 文法選択 Templates ────────────────────────
SENTAKU_FRONT = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type quiz">選択問題</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="quiz-question">{{問題}}</div>
  <div class="options">
    <div class="opt-btn">A. {{選択肢A}}</div>
    <div class="opt-btn">B. {{選択肢B}}</div>
    <div class="opt-btn">C. {{選択肢C}}</div>
    <div class="opt-btn">D. {{選択肢D}}</div>
  </div>
</div>
"""

SENTAKU_BACK = """
<div class="card-box">
  <div class="card-header">
    <span class="card-type quiz">選択問題</span>
    {{#課}}<span class="lesson-tag">{{課}}</span>{{/課}}
  </div>
  <div class="quiz-question">{{問題}}</div>
  <div class="options" id="ans-options">
    <div class="opt-btn" data-val="A">A. {{選択肢A}}</div>
    <div class="opt-btn" data-val="B">B. {{選択肢B}}</div>
    <div class="opt-btn" data-val="C">C. {{選択肢C}}</div>
    <div class="opt-btn" data-val="D">D. {{選択肢D}}</div>
  </div>

  {{#解説}}
  <div class="hint-block">
    <div class="hint-title">解説</div>
    <div class="hint-text">{{解説}}</div>
  </div>
  {{/解説}}
</div>
<script>
(function(){
  var ans = '{{正解}}';
  var opts = document.querySelectorAll('#ans-options .opt-btn');
  for (var i = 0; i < opts.length; i++) {
    var letter = opts[i].getAttribute('data-val');
    if (letter === ans) {
      opts[i].className = 'opt-btn correct';
    } else {
      opts[i].className = 'opt-btn wrong';
    }
  }
})();
</script>
"""


def lesson_deck(lesson_num):
    """Get sub-deck name: 文法::第01課"""
    return f"{DECK}::第{lesson_num:02d}課"


def build_ninshiki_notes(data):
    """Build 認識卡 notes from grammar_data.json"""
    notes = []
    for item in data:
        # 正面: 课号+句型名（课号确保唯一性，模板中可隐藏）
        front = f'{item["lesson"]} {item["title"]}'

        # 代表例句: 第一个例句
        rep_example = ""
        if item["examples"]:
            ex = item["examples"][0]
            rep_example = f'<div class="ex-jp">{ex["jp"]}</div>'
            if ex["cn"]:
                rep_example += f'<div class="ex-cn">{ex["cn"]}</div>'

        # 背面: 中文说明（截断过长的，取前几行关键内容）
        explanation = item["explanation"]
        # Clean up for display
        lines = [l for l in explanation.split("\n") if l.strip()]
        back_text = "\n".join(lines[:8])  # Max 8 lines for readability
        if len(lines) > 8:
            back_text += "\n……"

        # 例句一覧: 全部例句 HTML
        examples_html = ""
        for ex in item["examples"]:
            examples_html += f'<div class="ex-item"><div class="ex-jp">{ex["jp"]}</div>'
            if ex["cn"]:
                examples_html += f'<div class="ex-cn">{ex["cn"]}</div>'
            examples_html += '</div>'

        notes.append({
            "deckName": lesson_deck(item["lesson_num"]),
            "modelName": MODEL_NINSHIKI,
            "fields": {
                "正面": front,
                "代表例句": rep_example,
                "背面": back_text,
                "例句一覧": examples_html,
                "課": item["lesson"],
            },
            "options": {"allowDuplicate": False},
            "tags": [item["lesson"]],
        })

    return notes


def build_sentaku_notes(quizzes):
    """Build 選択問題 notes from grammar_quiz.json"""
    notes = []
    for q in quizzes:
        if not q["question"] or not q["answer"]:
            continue  # Skip unfilled entries
        if any(not o for o in q["options"]):
            continue

        # Map answer to A/B/C/D
        try:
            ans_idx = q["options"].index(q["answer"])
        except ValueError:
            print(f"  ⚠ {q['id']}: answer not in options, skipping")
            continue
        ans_letter = "ABCD"[ans_idx]

        # Extract lesson number for sub-deck
        import re as _re
        lnum = int(_re.search(r"\d+", q["lesson"]).group())

        notes.append({
            "deckName": lesson_deck(lnum),
            "modelName": MODEL_SENTAKU,
            "fields": {
                "問題": q["question"],
                "選択肢A": q["options"][0],
                "選択肢B": q["options"][1],
                "選択肢C": q["options"][2],
                "選択肢D": q["options"][3],
                "正解": ans_letter,
                "解説": q.get("hint", ""),
                "課": q["lesson"],
            },
            "options": {"allowDuplicate": False},
            "tags": [q["lesson"]],
        })

    return notes


def ensure_model(model_name, fields, templates):
    """Create or update a model"""
    existing = anki("modelNames")
    if model_name not in existing:
        anki("createModel",
             modelName=model_name,
             inOrderFields=fields,
             css=CSS,
             cardTemplates=templates)
        print(f"  + 模型「{model_name}」已创建")
    else:
        # Update fields
        current_fields = anki("modelFieldNames", modelName=model_name)
        for fname in fields:
            if fname not in current_fields:
                anki("modelFieldAdd", modelName=model_name,
                     fieldName=fname, index=len(current_fields))
                current_fields.append(fname)
                print(f"  + {model_name}: 字段「{fname}」已添加")

        # Update CSS + templates
        anki("updateModelStyling", model={"name": model_name, "css": CSS})
        tmpl_dict = {}
        for t in templates:
            tmpl_dict[t["Name"]] = {"Front": t["Front"], "Back": t["Back"]}
        anki("updateModelTemplates", model={
            "name": model_name, "templates": tmpl_dict
        })
        print(f"  ✓ 模型「{model_name}」已更新")


def add_notes(notes, label):
    """Batch add notes, return (added, skipped)"""
    if not notes:
        return 0, 0

    added = 0
    skipped = 0

    # Add in batches of 50
    batch_size = 50
    for i in range(0, len(notes), batch_size):
        batch = notes[i:i+batch_size]
        try:
            ids = anki("addNotes", notes=batch)
            for nid in ids:
                if nid:
                    added += 1
                else:
                    skipped += 1
        except Exception as e:
            print(f"  ⚠ {label} batch error: {e}")
            # Fall back to one-by-one
            for note in batch:
                try:
                    ids = anki("addNotes", notes=[note])
                    if ids and ids[0]:
                        added += 1
                    else:
                        skipped += 1
                except Exception:
                    skipped += 1

        sys.stdout.write(f"\r  {label}: [{min(i+batch_size, len(notes))}/{len(notes)}] +{added}")
        sys.stdout.flush()

    print()
    return added, skipped


def main():
    print("=" * 55)
    print("  文法 Anki — 語法認識 + 選択問題")
    print("=" * 55)

    # 1. Load data
    print("\n[1/4] 读取数据...")
    with open(GRAMMAR_DATA, "r", encoding="utf-8") as f:
        grammar_data = json.load(f)
    print(f"  語法認識: {len(grammar_data)} 个语法点")

    quiz_notes = []
    if os.path.exists(GRAMMAR_QUIZ):
        with open(GRAMMAR_QUIZ, "r", encoding="utf-8") as f:
            quiz_data = json.load(f)
        # Filter only filled entries
        filled = [q for q in quiz_data if q.get("question") and q.get("answer")]
        print(f"  選択問題: {len(filled)} / {len(quiz_data)} 已填写")
    else:
        quiz_data = []
        filled = []
        print("  選択問題: grammar_quiz.json 不存在，跳过")

    # 2. Connect
    if not wait_for_anki(5):
        print("\n✗ 请打开 Anki")
        return

    for profile in PROFILES:
        print(f"\n{'─' * 40}")
        print(f"  [{profile}]")
        print(f"{'─' * 40}")

        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(10)
        if not wait_for_anki(30):
            print(f"  ✗ 超时")
            continue

        # Sanity check
        nids = anki("findNotes", query='"deck:みんなの日本語初级1-2 単語"')
        print(f"  Profile 确认: {profile} ({len(nids)} vocab notes)")

        # 3. Create models
        print("\n[2/4] 创建模型...")

        # Clean old deck
        try:
            deck_names = anki("deckNames")
            to_delete = [d for d in deck_names if d == DECK or d.startswith(DECK + "::")]
            if to_delete:
                anki("deleteDecks", decks=to_delete, cardsToo=True)
                print(f"  已删除旧牌组 {DECK}")
                time.sleep(3)
                wait_for_anki(10)
        except Exception:
            pass

        anki("createDeck", deck=DECK)

        # Create sub-decks per lesson
        lessons = sorted(set(item["lesson_num"] for item in grammar_data))
        for lnum in lessons:
            anki("createDeck", deck=lesson_deck(lnum))
        print(f"  子牌组: {len(lessons)} 课")

        ensure_model(MODEL_NINSHIKI,
                     ["正面", "代表例句", "背面", "例句一覧", "課"],
                     [{"Name": "認識", "Front": NINSHIKI_FRONT, "Back": NINSHIKI_BACK}])

        ensure_model(MODEL_SENTAKU,
                     ["問題", "選択肢A", "選択肢B", "選択肢C", "選択肢D", "正解", "解説", "課"],
                     [{"Name": "選択", "Front": SENTAKU_FRONT, "Back": SENTAKU_BACK}])

        # 4. Build and add notes
        print("\n[3/4] 导入認識卡...")
        ninshiki_notes = build_ninshiki_notes(grammar_data)
        n_added, n_skipped = add_notes(ninshiki_notes, "認識")
        print(f"  → {n_added} 张新卡片, {n_skipped} 张跳过")

        if filled:
            print("\n[4/4] 导入選択卡...")
            sentaku_notes = build_sentaku_notes(quiz_data)
            s_added, s_skipped = add_notes(sentaku_notes, "選択")
            print(f"  → {s_added} 张新卡片, {s_skipped} 张跳过")
        else:
            print("\n[4/4] 選択卡: 无数据，跳过")

    # Switch back
    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)

    print(f"\n{'=' * 55}")
    print(f"  ✅ 导入完成！")
    print(f"  牌组: {DECK}")
    print(f"  認識卡: {len(grammar_data)} 个语法点")
    print(f"  選択卡: {len(filled)} 道选择题")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
