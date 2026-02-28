#!/usr/bin/env python3
"""
快速补充单词到两个 Profile
- 标记为「补充」
- 自动放到复习队列最前面（today's new cards）
- 无需音频

用法:
  python3 anki/add.py 食べる たべる 動II 吃
  python3 anki/add.py コンビニ コンビニ 名 便利店 --lesson 第51課
  python3 anki/add.py --file words.txt

words.txt 格式 (tab分隔):
  食べる	たべる	動II	吃
  コンビニ	コンビニ	名	便利店
"""
import json
import urllib.request
import os
import sys
import time
import argparse
import hashlib
import re
import base64
import urllib.parse

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

import unicodedata


def _is_kanji(ch):
    """Return True if ch is a CJK ideograph (kanji)."""
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
            or 0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF)


def _kata_to_hira(text):
    """Convert katakana to hiragana for comparison."""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x30A1 <= cp <= 0x30F6:
            result.append(chr(cp - 0x60))
        else:
            result.append(ch)
    return "".join(result)


def make_furigana(word, reading):
    """Generate Anki furigana format: 漢字[かんじ] from word and reading.

    Examples:
        make_furigana("弄びます", "もてあそびます") → " 弄[もてあそ]びます"
        make_furigana("食べる", "たべる") → " 食[た]べる"
        make_furigana("コンビニ", "コンビニ") → "コンビニ"  (no kanji, no change)
    """
    if not word or not reading:
        return word
    # If word == reading (pure kana), no furigana needed
    reading_hira = _kata_to_hira(reading)
    word_hira = _kata_to_hira(word)
    if word_hira == reading_hira:
        return word
    # If no kanji at all, return as-is
    if not any(_is_kanji(ch) for ch in word):
        return word

    # Build furigana: walk through word, group consecutive kanji,
    # match surrounding kana with reading to extract furigana portion
    parts = []  # list of (text, is_kanji)
    i = 0
    while i < len(word):
        if _is_kanji(word[i]):
            j = i
            while j < len(word) and _is_kanji(word[j]):
                j += 1
            parts.append((word[i:j], True))
            i = j
        else:
            j = i
            while j < len(word) and not _is_kanji(word[j]):
                j += 1
            parts.append((word[i:j], False))
            i = j

    # Match kana parts against reading to determine furigana for kanji parts
    result = []
    r_pos = 0  # position in reading_hira
    for idx, (text, is_k) in enumerate(parts):
        if not is_k:
            # Kana part: advance r_pos past matching chars
            text_hira = _kata_to_hira(text)
            r_pos += len(text_hira)
            result.append(text)
        else:
            # Kanji part: find where the next kana part starts in reading
            # Look ahead for next kana part to determine boundary
            next_kana = ""
            for future_text, future_is_k in parts[idx + 1:]:
                if not future_is_k:
                    next_kana = _kata_to_hira(future_text)
                    break

            if next_kana:
                # Find next_kana in reading_hira starting from r_pos
                boundary = reading_hira.find(next_kana, r_pos)
                if boundary == -1:
                    # Fallback: just use remaining reading
                    furi = reading[r_pos:]
                    r_pos = len(reading)
                else:
                    furi = reading[r_pos:boundary]
                    r_pos = boundary
            else:
                # Last part: take all remaining reading
                furi = reading[r_pos:]
                r_pos = len(reading)

            # Anki furigana format: space before kanji[reading]
            result.append(f" {text}[{furi}]")

    return "".join(result)



ANKI_URL = "http://localhost:8765"
VOICEVOX_URL = "http://127.0.0.1:50021"
DECK = "補充単語"
MODEL = "みんなの日本語"
PROFILES = ["szmz", "czh"]

# VOICEVOX state
_voicevox_available = None
_speaker_word = None  # 琴詠ニア (単語)
_speaker_example = None  # 剣崎雌雄 (例句)


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
    for i in range(timeout):
        try:
            anki("version")
            return True
        except Exception:
            time.sleep(1)
    return False


def check_voicevox():
    """Check if VOICEVOX is running, resolve speaker IDs"""
    global _voicevox_available, _speaker_word, _speaker_example
    if _voicevox_available is not None:
        return _voicevox_available
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/speakers")
        resp = _opener.open(req, timeout=3)
        speakers = json.loads(resp.read())
        for s in speakers:
            if "琴詠ニア" in s["name"]:
                _speaker_word = s["styles"][0]["id"]
            if "剣崎雌雄" in s["name"]:
                _speaker_example = s["styles"][0]["id"]
        _voicevox_available = _speaker_word is not None
    except Exception:
        _voicevox_available = False
    return _voicevox_available


def generate_word_audio(text):
    """Generate audio for a word via VOICEVOX 琴詠ニア, return (filename, b64) or None"""
    if not _voicevox_available or _speaker_word is None:
        return None
    return _synthesize(text, _speaker_word, "tts_word_")


def generate_example_audio(text):
    """Generate audio for an example sentence via VOICEVOX 剣崎雌雄, return (filename, b64) or None"""
    if not _voicevox_available or _speaker_example is None:
        return None
    return _synthesize(text, _speaker_example, "tts_ex_")


def _synthesize(text, speaker_id, prefix):
    """Shared VOICEVOX synthesis logic."""
    # Clean text: strip HTML tags and furigana brackets
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r" (\S+)\[([^\]]+)\]", r"\1", clean)
    clean = re.sub(r"\[([^\]]*)\]", "", clean)
    clean = clean.strip()
    if not clean:
        return None
    try:
        h = hashlib.md5(clean.encode("utf-8")).hexdigest()[:10]
        filename = f"{prefix}{h}.wav"
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
    except Exception:
        return None


def add_word(word, reading, pos, meaning, lesson="補充", example="", example_cn=""):
    """Add a single word to current profile"""
    jp_field = make_furigana(word, reading)

    # Try VOICEVOX audio generation
    audio_field = ""
    result = generate_word_audio(word)
    if result:
        filename, b64 = result
        try:
            anki("storeMediaFile", filename=filename, data=b64)
            audio_field = f"[sound:{filename}]"
        except Exception:
            pass

    # Try example sentence audio (剣崎雌雄)
    example_audio_field = ""
    if example:
        result = generate_example_audio(example)
        if result:
            filename, b64 = result
            try:
                anki("storeMediaFile", filename=filename, data=b64)
                example_audio_field = filename
            except Exception:
                pass

    try:
        ids = anki("addNotes", notes=[{
            "deckName": DECK,
            "modelName": MODEL,
            "fields": {
                "日文": jp_field,
                "音调核": "",
                "词性": pos,
                "基本形": "",
                "外来语": "",
                "中文": meaning,
                "音频": audio_field,
                "是否需要从汉字到假名": "1" if jp_field != reading else "",
                "是否需要缩小日文": "",
                "是否需要缩小假名": "",
                "是否需要缩小中文": "",
                "例句": example,
                "課": lesson,
                "例句翻译": example_cn,
                "例句音频": example_audio_field,
                "笔记": "",
            },
            "options": {"allowDuplicate": False},
            "tags": [lesson, pos, "補充"],
        }])
        if ids and ids[0]:
            note_id = ids[0]
            # Reposition to front of new card queue (position 0 = next new card)
            cards = anki("findCards", query=f"nid:{note_id} is:new")
            if cards:
                anki("forgetCards", cards=cards)
                # Set due position to 0 so they appear first
                anki("setSpecificValueOfCard", card=cards[0],
                     keys=["due"], newValues=[0])
            return True, word
        return False, f"{word} (重复)"
    except Exception as e:
        return False, f"{word} ({e})"


def main():
    parser = argparse.ArgumentParser(description="补充单词")
    parser.add_argument("words", nargs="*", help="日文 读音 词性 中文")
    parser.add_argument("--lesson", default="補充", help="课号标签")
    parser.add_argument("--file", "-f", help="从文件批量导入 (tab分隔)")
    parser.add_argument("--example", "-e", default="", help="例句")
    parser.add_argument("--example-cn", default="", help="例句中文翻译")
    args = parser.parse_args()

    # Parse words
    word_list = []
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 4:
                    word_list.append(parts[:4] + [args.lesson])
    elif len(args.words) >= 4:
        word_list.append([args.words[0], args.words[1], args.words[2],
                          " ".join(args.words[3:]), args.lesson])
    else:
        print("用法: python3 add.py 食べる たべる 動II 吃")
        print("      python3 add.py --file words.txt")
        return

    if not wait_for_anki(5):
        print("✗ 请打开 Anki")
        return

    # Check VOICEVOX (optional)
    if check_voicevox():
        print(f"  VOICEVOX OK (琴詠ニア: {_speaker_word})")
    else:
        print("  VOICEVOX not available, skipping audio generation")

    profiles = anki("getProfiles")

    for profile in PROFILES:
        if profile not in profiles:
            continue

        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(10)
        if not wait_for_anki():
            print(f"✗ {profile} 切换失败")
            continue
        # Sanity check: verify profile actually switched
        nids = anki("findNotes", query='"deck:みんなの日本語初级1-2 単語"')
        print(f"  {profile}: {len(nids)} notes (sanity check)")

        added = 0
        for w in word_list:
            ok, msg = add_word(w[0], w[1], w[2], w[3], w[4] if len(w) > 4 else args.lesson, args.example, args.example_cn)
            if ok:
                added += 1

        print(f"  {profile}: +{added} 个词")

    # Switch back
    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(10)
    wait_for_anki()

    print(f"\n✅ {len(word_list)} 个词已补充到两个 Profile")
    print("  标记: 補充 | 优先出现在新卡片队列")


if __name__ == "__main__":
    main()
