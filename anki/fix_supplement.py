#!/usr/bin/env python3
"""一次性脚本：為補充単語 (1) 回填日文字段furigana (2) 例句TTS音频（剣崎雌雄）"""
import json
import urllib.request
import urllib.parse
import os
import sys
import time
import hashlib
import base64
import re

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
VOICEVOX_URL = "http://127.0.0.1:50021"
PROFILES = ["szmz", "czh"]

# ── word → reading 映射（用于生成 furigana）──
READINGS = {
    "弄びます": "もてあそびます",
    "お年玉": "おとしだま",
    "黙ります": "だまります",
    "許します": "ゆるします",
    "突き止めます": "つきとめます",
    "裏切ります": "うらぎります",
    "裏切り者": "うらぎりもの",
    "お小遣い": "おこづかい",
    "落ち着きます": "おちつきます",
    "係の人": "かかりのひと",
    "趣味": "しゅみ",
    "日記": "にっき",
    "ギター": "ギター",
    "歌": "うた",
    "係長": "かかりちょう",
    "そば": "そば",
    "壁": "かべ",
    "裏": "うら",
    "北": "きた",
    "弾きます": "ひきます",
    "歌います": "うたいます",
    "集めます": "あつめます",
    "捨てます": "すてます",
    "払います": "はらいます",
    "見学します": "けんがくします",
    "入場します": "にゅうじょうします",
    "利用します": "りようします",
    "注文します": "ちゅうもんします",
    "並べます": "ならべます",
    "置きます": "おきます",
    "泊まります": "とまります",
    "安い": "やすい",
    "にぎやか": "にぎやか",
    "特に": "とくに",
    "もうすぐ": "もうすぐ",
    "どんな": "どんな",
    "ほんとうですか": "ほんとうですか",
    "おいくら": "おいくら",
    "階段": "かいだん",
    "山": "やま",
    "勧める": "すすめる",
    "進める": "すすめる",
    "薦める": "すすめる",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add import make_furigana


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


def wait(timeout=30):
    for _ in range(timeout):
        try:
            anki("version")
            return True
        except Exception:
            time.sleep(1)
    return False


def strip_furigana(text):
    """Remove Anki furigana markup to get clean text for TTS."""
    text = re.sub(r" (\S+)\[([^\]]+)\]", r"\1", text)
    return text.strip()


def find_speaker(name_part):
    """Find VOICEVOX speaker ID by name substring."""
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/speakers")
        resp = _opener.open(req, timeout=5)
        speakers = json.loads(resp.read())
        for s in speakers:
            if name_part in s["name"]:
                return s["styles"][0]["id"]
    except Exception:
        pass
    return None


def generate_tts(text, speaker_id):
    """Generate TTS audio, return (filename, base64) or None."""
    clean = strip_furigana(text)
    if not clean:
        return None
    try:
        h = hashlib.md5(clean.encode("utf-8")).hexdigest()[:10]
        filename = f"tts_ex_{h}.wav"
        encoded = urllib.parse.quote(clean)
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
        wav = resp.read()
        b64 = base64.b64encode(wav).decode("utf-8")
        return filename, b64
    except Exception as e:
        print(f"    TTS error: {e}")
        return None


def process_profile(speaker_id):
    nids = anki("findNotes", query="deck:補充単語")
    if not nids:
        return 0, 0
    infos = anki("notesInfo", notes=nids)
    furi_count = 0
    tts_count = 0

    for n in infos:
        jp_raw = n["fields"]["日文"]["value"]
        updates = {}

        # ── 1. Furigana 回填 ──
        # Strip any existing furigana to get clean word
        clean_word = strip_furigana(jp_raw)
        reading = READINGS.get(clean_word, "")
        if reading and clean_word == jp_raw:
            # Currently plain text, needs furigana
            new_jp = make_furigana(clean_word, reading)
            if new_jp != clean_word:
                updates["日文"] = new_jp
                furi_count += 1

        # ── 2. 例句 TTS ──
        example = n["fields"].get("例句", {}).get("value", "")
        ex_audio = n["fields"].get("例句音频", {}).get("value", "")
        if example and not ex_audio:
            result = generate_tts(example, speaker_id)
            if result:
                filename, b64 = result
                anki("storeMediaFile", filename=filename, data=b64)
                updates["例句音频"] = f"[sound:{filename}]"
                tts_count += 1

        if updates:
            anki("updateNoteFields", note={
                "id": n["noteId"],
                "fields": updates
            })

    return furi_count, tts_count


def main():
    if not wait(5):
        print("✗ 请打开 Anki")
        return

    speaker_id = find_speaker("剣崎雌雄")
    if speaker_id is None:
        print("✗ VOICEVOX 未运行或找不到剣崎雌雄")
        return
    print(f"  VOICEVOX: 剣崎雌雄 (speaker={speaker_id})")

    for profile in PROFILES:
        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(5)
        if not wait():
            print(f"  ✗ {profile} 超时")
            continue
        furi, tts = process_profile(speaker_id)
        print(f"  ✓ {profile}: furigana {furi} 个, 例句音频 {tts} 个")

    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)
    print("✅ 完成")


if __name__ == "__main__":
    main()
