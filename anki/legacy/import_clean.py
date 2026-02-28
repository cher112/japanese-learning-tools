#!/usr/bin/env python3
"""
从干净的 单词.md 导入 Anki「初级1-2」牌组 + 生成 TTS
"""
import json
import re
import urllib.request
import base64
import time
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ANKI_URL = "http://localhost:8765"
DECK = "初级1-2"
MODEL = "日语单词卡片"

TTS_URL = "https://www.dmxapi.cn/v1/audio/speech"
TTS_KEY = "sk-xSnH2iKopoiPDZp78UBSDTHi4iugbv3VbXT3NlanJ8A3RF8t"
TTS_MODEL = "speech-2.6-hd"
TTS_VOICE = "female-shaonv"


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


def tts(text):
    payload = json.dumps({"model": TTS_MODEL, "voice": TTS_VOICE, "input": text})
    req = urllib.request.Request(TTS_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {TTS_KEY}"})
    resp = urllib.request.urlopen(req, timeout=30)
    return base64.b64encode(resp.read()).decode("utf-8")


def parse_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    words = []
    lesson = ""
    for line in content.split("\n"):
        m = re.match(r"^##\s+(第\d+課)", line)
        if m:
            lesson = m.group(1)
            continue
        if not line.startswith("|") or line.startswith("|--") or line.startswith("| 日语"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 4 or not cells[0]:
            continue
        words.append({
            "日语": cells[0], "读音": cells[1], "词性": cells[2],
            "中文": cells[3], "课": lesson
        })
    return words


def main():
    print("=" * 50)
    print("  初级1-2 干净词汇 → Anki 导入")
    print("=" * 50)

    # 1. Parse
    words = parse_md(os.path.join(BASE_DIR, "单词.md"))
    print(f"✓ 解析出 {len(words)} 个单词")

    # 2. Connect
    try:
        anki("version")
        print("✓ AnkiConnect 连接成功")
    except Exception:
        print("✗ 请打开 Anki")
        return

    anki("createDeck", deck=DECK)

    # Ensure 音声 field
    fields = anki("modelFieldNames", modelName=MODEL)
    if "音声" not in fields:
        anki("modelFieldAdd", modelName=MODEL, fieldName="音声", index=6)

    # 3. Import - one by one to handle duplicates gracefully
    added = 0
    skipped = 0
    for i, w in enumerate(words):
        try:
            ids = anki("addNotes", notes=[{
                "deckName": DECK, "modelName": MODEL,
                "fields": {
                    "日语": w["日语"], "读音": w["读音"], "中文": w["中文"],
                    "词性": w["词性"], "例句": "", "课": w["课"], "音声": ""
                },
                "options": {"allowDuplicate": False},
                "tags": [w["课"], w["词性"]],
            }])
            if ids and ids[0]:
                added += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1

    print(f"✓ Anki 导入: {added} 张新卡片, {skipped} 张跳过")

    # 4. TTS
    print(f"\n生成 TTS 语音...")
    note_ids = anki("findNotes", query=f'deck:"{DECK}"')
    notes_info = anki("notesInfo", notes=note_ids)

    gen = 0
    fail = 0
    for i, note in enumerate(notes_info):
        f = note["fields"]
        word = f["日语"]["value"]
        reading = f.get("读音", {}).get("value", "")
        audio = f.get("音声", {}).get("value", "")

        if audio and "[sound:" in audio:
            continue

        tts_text = reading if reading else word
        if not tts_text or len(tts_text) > 30:
            continue

        fn = f"jp_tts_{word.replace('/', '_').replace('～', '').replace(' ', '')}.mp3"
        sys.stdout.write(f"\r  [{i+1}/{len(notes_info)}] {word}...")
        sys.stdout.flush()

        try:
            audio_b64 = tts(tts_text)
            anki("storeMediaFile", filename=fn, data=audio_b64)
            anki("updateNoteFields", note={
                "id": note["noteId"], "fields": {"音声": f"[sound:{fn}]"}
            })
            gen += 1
            time.sleep(0.25)
        except Exception:
            fail += 1

    print(f"\n✓ TTS: {gen} 条生成, {fail} 条失败")
    print(f"\n✅ 完成！牌组「{DECK}」共 {len(notes_info)} 张卡片")


if __name__ == "__main__":
    main()
