#!/usr/bin/env python3
"""
清除旧TTS + 用 tts-1 alloy 重新生成全部语音
"""
import json
import urllib.request
import base64
import time
import sys

ANKI_URL = "http://localhost:8765"
DECK = "初级1-2"
DECK2 = "日语N5单词"

TTS_URL = "https://www.dmxapi.cn/v1/audio/speech"
TTS_KEY = "sk-xSnH2iKopoiPDZp78UBSDTHi4iugbv3VbXT3NlanJ8A3RF8t"
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"


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


def process_deck(deck_name):
    print(f"\n{'='*50}")
    print(f"  处理牌组: {deck_name}")
    print(f"{'='*50}")

    note_ids = anki("findNotes", query=f'deck:"{deck_name}"')
    if not note_ids:
        print(f"  牌组为空，跳过")
        return

    notes = anki("notesInfo", notes=note_ids)
    print(f"  共 {len(notes)} 张卡片")

    # Step 1: 清除所有旧音频
    print("  清除旧 TTS...")
    cleared = 0
    for note in notes:
        audio = note["fields"].get("音声", {}).get("value", "")
        if audio:
            try:
                anki("updateNoteFields", note={
                    "id": note["noteId"], "fields": {"音声": ""}
                })
                cleared += 1
            except:
                pass
    print(f"  ✓ 清除了 {cleared} 条旧音频")

    # Step 2: 重新生成
    print(f"  用 {TTS_MODEL} / {TTS_VOICE} 生成新 TTS...")
    gen = 0
    fail = 0
    skip = 0

    for i, note in enumerate(notes):
        f = note["fields"]
        word = f["日语"]["value"]
        reading = f.get("读音", {}).get("value", "")

        # 确定 TTS 文本：优先用读音（假名），否则用日语原文
        tts_text = reading if reading else word

        # 跳过太短或含特殊符号的
        clean = tts_text.replace("～", "").replace("＋", "").replace("・", "").strip()
        if len(clean) < 1 or len(tts_text) > 40:
            skip += 1
            continue
        # 跳过纯语法标记
        if tts_text.startswith("～") and len(clean) <= 2:
            skip += 1
            continue

        fn = f"jp_{word.replace('/', '_').replace('～', '').replace(' ', '').replace('＋', '')}.mp3"

        sys.stdout.write(f"\r  [{i+1}/{len(notes)}] {word}...")
        sys.stdout.flush()

        try:
            audio_b64 = tts(tts_text)
            anki("storeMediaFile", filename=fn, data=audio_b64)
            anki("updateNoteFields", note={
                "id": note["noteId"], "fields": {"音声": f"[sound:{fn}]"}
            })
            gen += 1
            time.sleep(0.2)
        except Exception as e:
            fail += 1

    print(f"\n  ✓ 生成: {gen}  跳过: {skip}  失败: {fail}")


def main():
    try:
        anki("version")
        print("✓ AnkiConnect 连接成功")
    except:
        print("✗ 请打开 Anki")
        return

    process_deck(DECK)
    process_deck(DECK2)

    print(f"\n✅ 全部完成！TTS 模型: {TTS_MODEL} / 音色: {TTS_VOICE}")


if __name__ == "__main__":
    main()
