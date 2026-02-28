#!/usr/bin/env python3
"""
为「みんなの日本語」卡片的例句生成 TTS 音频（WhiteCUL 楽しい）。
- 遍历有例句但没例句音频的卡片
- VOICEVOX WhiteCUL 生成 WAV
- 存纯文件名到例句音频字段（不带 [sound:]，保持 click-to-play）
- 操作两个 Profile（szmz / czh）

用法:
  python3 anki/tts_minna_examples.py                # 生成全部
  python3 anki/tts_minna_examples.py --dry-run      # 预览
  python3 anki/tts_minna_examples.py --limit 10     # 只处理前10个
"""
import json
import urllib.request
import os
import re
import time
import hashlib
import base64
import argparse
import urllib.parse

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
VOICEVOX_URL = "http://127.0.0.1:50021"
DECK = "みんなの日本語初级1-2 単語"
PROFILES = ["szmz", "czh"]

SPEAKER_ID = None  # WhiteCUL 楽しい, resolved at runtime


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


def resolve_speaker():
    """Find WhiteCUL 楽しい speaker ID from VOICEVOX"""
    global SPEAKER_ID
    req = urllib.request.Request(f"{VOICEVOX_URL}/speakers")
    resp = _opener.open(req, timeout=5)
    speakers = json.loads(resp.read())
    for s in speakers:
        if "WhiteCUL" in s["name"]:
            for style in s["styles"]:
                if "楽しい" in style["name"]:
                    SPEAKER_ID = style["id"]
                    return SPEAKER_ID
            # fallback to first style
            SPEAKER_ID = s["styles"][0]["id"]
            return SPEAKER_ID
    return None


def clean_for_tts(text):
    """Remove furigana markup and HTML, extract plain text for TTS"""
    text = re.sub(r"<[^>]+>", "", text)
    # furigana: ' 食[た]べる' → '食べる'
    text = re.sub(r" (\S+)\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]", "", text)
    text = re.sub(r"\[sound:[^\]]+\]", "", text)
    return text.strip()


def generate_audio(text, speaker_id):
    """Generate WAV bytes via VOICEVOX"""
    encoded = urllib.parse.quote(text)
    # audio_query
    req = urllib.request.Request(
        f"{VOICEVOX_URL}/audio_query?text={encoded}&speaker={speaker_id}",
        data=b"", method="POST")
    resp = _opener.open(req)
    query = json.loads(resp.read())
    # synthesis
    req = urllib.request.Request(
        f"{VOICEVOX_URL}/synthesis?speaker={speaker_id}",
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    return resp.read()


def make_filename(text):
    """Deterministic filename from clean text"""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    return f"tts_wcul_{h}.wav"


def process_profile(dry_run=False, limit=0):
    """Generate TTS for cards with 例句 but no 例句音频. Returns count."""
    nids = anki("findNotes", query=f'"deck:{DECK}"')
    if not nids:
        print("  No notes found")
        return 0
    infos = anki("notesInfo", notes=nids)
    count = 0
    for note in infos:
        example = note["fields"].get("例句", {}).get("value", "")
        if not example.strip():
            continue
        ex_audio = note["fields"].get("例句音频", {}).get("value", "")
        if ex_audio.strip():
            continue  # Already has audio

        text = clean_for_tts(example)
        if not text:
            continue

        filename = make_filename(text)
        jp_word = note["fields"].get("日文", {}).get("value", "")[:15]
        print(f"  {jp_word} → {filename}", end="")

        if dry_run:
            print(" (dry-run)")
            count += 1
            if limit and count >= limit:
                break
            continue

        try:
            wav_data = generate_audio(text, SPEAKER_ID)
            b64 = base64.b64encode(wav_data).decode("utf-8")
            anki("storeMediaFile", filename=filename, data=b64)
            # 纯文件名，不带 [sound:]，保持 click-to-play
            anki("updateNoteFields", note={
                "id": note["noteId"],
                "fields": {"例句音频": filename}
            })
            print(" OK")
            count += 1
        except Exception as e:
            print(f" FAIL: {e}")

        if limit and count >= limit:
            break

    return count


def main():
    parser = argparse.ArgumentParser(description="みんなの日本語 例句 TTS（WhiteCUL）")
    parser.add_argument("--dry-run", action="store_true", help="预览不生成")
    parser.add_argument("--limit", type=int, default=0, help="最多处理几个")
    parser.add_argument("--profile", help="只处理指定 profile (szmz/czh)")
    args = parser.parse_args()

    # Check VOICEVOX
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/version")
        _opener.open(req, timeout=3)
        print("VOICEVOX OK")
    except Exception:
        print("✗ VOICEVOX 未运行 (http://127.0.0.1:50021)")
        return

    sid = resolve_speaker()
    if not sid:
        print("✗ WhiteCUL not found in VOICEVOX speakers")
        return
    print(f"  WhiteCUL 楽しい: speaker_id={sid}")

    if not wait(5):
        print("✗ 请打开 Anki")
        return

    profiles = [args.profile] if args.profile else PROFILES
    for profile in profiles:
        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(10)
        if not wait():
            print(f"  ✗ {profile} 超时")
            continue
        print(f"\n=== {profile} ===")
        count = process_profile(dry_run=args.dry_run, limit=args.limit)
        print(f"  Generated: {count}")

    # Switch back
    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)
    prefix = "[dry-run] " if args.dry_run else ""
    print(f"\n{prefix}✅ 例句 TTS 完成")


if __name__ == "__main__":
    main()
