#!/usr/bin/env python3
"""
VOICEVOX TTS for Anki cards
  - 単語音声: 琴詠ニア (kotoyomi nia)
  - 例句音声: 剣崎雌雄 (kenzaki mesuo)

Usage:
  # Generate word audio for 補充単語 (琴詠ニア)
  python3 anki/tts.py --words --deck 補充単語

  # Generate example sentence audio (剣崎雌雄)
  python3 anki/tts.py --examples --deck みんなの日本語

  # Both decks, all profiles
  python3 anki/tts.py --words --deck 補充単語 --all-profiles
  python3 anki/tts.py --examples --all-profiles

  # List available speakers
  python3 anki/tts.py --list-speakers
"""
import json
import urllib.request
import os
import sys
import hashlib
import re
import time
import base64
import argparse

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
VOICEVOX_URL = "http://127.0.0.1:50021"
MODEL = "みんなの日本語"
PROFILES = ["szmz", "czh"]

# Speaker IDs — will be resolved at runtime from /speakers
SPEAKER_WORD = None   # 琴詠ニア
SPEAKER_EXAMPLE = None  # 剣崎雌雄


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


def voicevox_get(path):
    req = urllib.request.Request(f"{VOICEVOX_URL}{path}")
    resp = _opener.open(req)
    return json.loads(resp.read())


def voicevox_post(path, data=None, content_type="application/json"):
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(f"{VOICEVOX_URL}{path}", data=body,
                                 headers={"Content-Type": content_type} if body else {})
    if not body:
        req = urllib.request.Request(f"{VOICEVOX_URL}{path}", data=b"",
                                     method="POST")
    resp = _opener.open(req)
    return resp.read()


def resolve_speakers():
    """Find speaker IDs for 琴詠ニア and 剣崎雌雄"""
    global SPEAKER_WORD, SPEAKER_EXAMPLE
    speakers = voicevox_get("/speakers")
    for s in speakers:
        name = s["name"]
        if "琴詠ニア" in name:
            # Use the first style
            SPEAKER_WORD = s["styles"][0]["id"]
        if "剣崎雌雄" in name:
            SPEAKER_EXAMPLE = s["styles"][0]["id"]
    return SPEAKER_WORD, SPEAKER_EXAMPLE


def list_speakers():
    speakers = voicevox_get("/speakers")
    for s in speakers:
        print(f"\n{s['name']}:")
        for st in s["styles"]:
            print(f"  [{st['id']}] {st['name']}")


def clean_text(text):
    """Remove furigana markup and HTML tags, extract plain text for TTS"""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Handle furigana: 食[た]べる → 食べる (keep kanji, remove bracket content)
    # But also handle ruby: <ruby>食<rt>た</rt></ruby> → 食
    text = re.sub(r"\[([^\]]*)\]", "", text)
    # Remove sound references
    text = re.sub(r"\[sound:[^\]]+\]", "", text)
    # Clean whitespace
    text = text.strip()
    return text


def generate_audio(text, speaker_id):
    """Generate WAV audio via VOICEVOX"""
    # Step 1: audio_query
    encoded = urllib.parse.quote(text)
    query_url = f"/audio_query?text={encoded}&speaker={speaker_id}"
    req = urllib.request.Request(f"{VOICEVOX_URL}{query_url}", data=b"", method="POST")
    resp = _opener.open(req)
    query = json.loads(resp.read())

    # Step 2: synthesis
    synth_url = f"/synthesis?speaker={speaker_id}"
    req = urllib.request.Request(f"{VOICEVOX_URL}{synth_url}",
                                 data=json.dumps(query).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    return resp.read()  # WAV bytes


def make_filename(prefix, text):
    """Generate deterministic filename from text"""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    return f"tts_{prefix}_{h}.wav"


def process_words(deck, dry_run=False):
    """Generate word audio for cards missing 音频 field"""
    print(f"\n--- 単語音声 ({deck}) ---")
    if SPEAKER_WORD is None:
        print("  ! 琴詠ニア not found in VOICEVOX speakers")
        return 0

    # Find notes with empty 音频
    note_ids = anki("findNotes", query=f'"deck:{deck}" 音频:')
    if not note_ids:
        # Try broader: all notes in deck
        note_ids = anki("findNotes", query=f'"deck:{deck}"')

    if not note_ids:
        print("  No notes found")
        return 0

    notes_info = anki("notesInfo", notes=note_ids)
    count = 0
    for note in notes_info:
        audio_val = note["fields"].get("音频", {}).get("value", "")
        if audio_val.strip():
            continue  # Already has audio

        jp_text = note["fields"].get("日文", {}).get("value", "")
        if not jp_text:
            continue

        text = clean_text(jp_text)
        if not text:
            continue

        filename = make_filename("word", text)
        print(f"  {text} → {filename}", end="")

        if dry_run:
            print(" (dry-run)")
            count += 1
            continue

        try:
            wav_data = generate_audio(text, SPEAKER_WORD)
            b64 = base64.b64encode(wav_data).decode("utf-8")
            anki("storeMediaFile", filename=filename, data=b64)
            anki("updateNoteFields", note={
                "id": note["noteId"],
                "fields": {"音频": f"[sound:{filename}]"}
            })
            print(" OK")
            count += 1
        except Exception as e:
            print(f" FAIL: {e}")

    print(f"  Generated: {count}")
    return count


def process_examples(deck, dry_run=False):
    """Generate example sentence audio for cards with 例句 but no 例句音频"""
    print(f"\n--- 例句音声 ({deck}) ---")
    if SPEAKER_EXAMPLE is None:
        print("  ! 剣崎雌雄 not found in VOICEVOX speakers")
        return 0

    note_ids = anki("findNotes", query=f'"deck:{deck}"')
    if not note_ids:
        print("  No notes found")
        return 0

    notes_info = anki("notesInfo", notes=note_ids)
    count = 0
    for note in notes_info:
        example = note["fields"].get("例句", {}).get("value", "")
        if not example.strip():
            continue

        ex_audio = note["fields"].get("例句音频", {}).get("value", "")
        if ex_audio.strip():
            continue  # Already has audio

        text = clean_text(example)
        if not text:
            continue

        filename = make_filename("ex", text)
        print(f"  {text[:30]}... → {filename}", end="")

        if dry_run:
            print(" (dry-run)")
            count += 1
            continue

        try:
            wav_data = generate_audio(text, SPEAKER_EXAMPLE)
            b64 = base64.b64encode(wav_data).decode("utf-8")
            anki("storeMediaFile", filename=filename, data=b64)
            anki("updateNoteFields", note={
                "id": note["noteId"],
                "fields": {"例句音频": f"[sound:{filename}]"}
            })
            print(" OK")
            count += 1
        except Exception as e:
            print(f" FAIL: {e}")

    print(f"  Generated: {count}")
    return count


def wait_for_anki(timeout=10):
    for _ in range(timeout):
        try:
            anki("version")
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    import urllib.parse  # needed for generate_audio

    parser = argparse.ArgumentParser(description="VOICEVOX TTS for Anki")
    parser.add_argument("--words", action="store_true", help="Generate word audio (琴詠ニア)")
    parser.add_argument("--examples", action="store_true", help="Generate example audio (剣崎雌雄)")
    parser.add_argument("--deck", default="補充単語", help="Target deck name")
    parser.add_argument("--all-profiles", action="store_true", help="Run on all profiles")
    parser.add_argument("--list-speakers", action="store_true", help="List VOICEVOX speakers")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    # Check VOICEVOX
    try:
        voicevox_get("/version")
        print("VOICEVOX OK")
    except Exception:
        print("! VOICEVOX not running (http://127.0.0.1:50021)")
        print("  Please start VOICEVOX first")
        return

    if args.list_speakers:
        list_speakers()
        return

    if not args.words and not args.examples:
        print("Specify --words and/or --examples")
        return

    # Check Anki
    if not wait_for_anki(5):
        print("! Anki not running")
        return

    # Resolve speakers
    resolve_speakers()
    print(f"  琴詠ニア: speaker_id={SPEAKER_WORD}")
    print(f"  剣崎雌雄: speaker_id={SPEAKER_EXAMPLE}")

    profiles = PROFILES if args.all_profiles else [None]

    for profile in profiles:
        if profile:
            try:
                anki("loadProfile", name=profile)
            except Exception:
                pass
            time.sleep(3)
            if not wait_for_anki():
                print(f"! {profile} switch failed")
                continue
            print(f"\n=== Profile: {profile} ===")

        if args.words:
            process_words(args.deck, dry_run=args.dry_run)
        if args.examples:
            process_examples(args.deck, dry_run=args.dry_run)

    # Switch back
    if args.all_profiles:
        try:
            anki("loadProfile", name="szmz")
        except Exception:
            pass
        time.sleep(2)

    print("\nDone!")


if __name__ == "__main__":
    main()
