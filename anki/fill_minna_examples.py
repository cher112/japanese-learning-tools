#!/usr/bin/env python3
"""
从 anki/examples/lesson_XX.json 读取例句数据，填入「みんなの日本語」卡片。
- 匹配 日文 字段（去掉 furigana 后与 JSON key 比对）
- 填入 例句 + 例句翻译
- 跳过已有例句的卡片
- 操作两个 Profile（szmz / czh）

用法:
  python3 anki/fill_minna_examples.py                  # 填入所有已有 JSON 的课
  python3 anki/fill_minna_examples.py --lessons 1-5    # 只填前5课
  python3 anki/fill_minna_examples.py --dry-run        # 预览不写入
"""
import json
import urllib.request
import os
import re
import time
import argparse
import glob

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
DECK = "みんなの日本語初级1-2 単語"
PROFILES = ["szmz", "czh"]
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")


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
    """Remove furigana markup: ' 食[た]べます' → '食べます'
    Handles adjacent kanji: '先[せん]生[せい]' → '先生'"""
    text = re.sub(r"\[[^\]]+\]", "", text)  # Remove all [reading]
    text = text.replace(" ", "")  # Remove furigana marker spaces
    return text.strip()


def load_examples(lesson_range=None):
    """Load all lesson JSON files into a single dict {word: {jp, cn}}"""
    all_examples = {}
    pattern = os.path.join(EXAMPLES_DIR, "lesson_*.json")
    files = sorted(glob.glob(pattern))
    for fpath in files:
        basename = os.path.basename(fpath)
        # Extract lesson number from filename
        m = re.match(r"lesson_(\d+)\.json", basename)
        if not m:
            continue
        lesson_num = int(m.group(1))
        if lesson_range and lesson_num not in lesson_range:
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_examples.update(data)
        print(f"  loaded {basename}: {len(data)} entries")
    return all_examples


def parse_lesson_range(s):
    """Parse '1-5' or '1,3,5' or '7' into a set of ints"""
    result = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        else:
            result.add(int(part))
    return result


def fill_profile(examples, dry_run=False):
    """Fill examples for current profile. Returns (updated, skipped, missing)."""
    nids = anki("findNotes", query=f'"deck:{DECK}"')
    if not nids:
        return 0, 0, 0
    infos = anki("notesInfo", notes=nids)
    updated = 0
    skipped = 0
    missing = 0
    for n in infos:
        jp_raw = n["fields"]["日文"]["value"]
        clean = strip_furigana(jp_raw)
        entry = examples.get(clean)
        if not entry:
            missing += 1
            continue
        # Skip if already has example
        existing = n["fields"].get("例句", {}).get("value", "")
        if existing.strip():
            skipped += 1
            continue
        if dry_run:
            print(f"    [dry-run] {clean} → {entry['jp'][:30]}...")
            updated += 1
            continue
        fields = {"例句": entry["jp"]}
        if entry.get("cn"):
            fields["例句翻译"] = entry["cn"]
        anki("updateNoteFields", note={
            "id": n["noteId"],
            "fields": fields,
        })
        updated += 1
    return updated, skipped, missing


def main():
    parser = argparse.ArgumentParser(description="填充みんなの日本語例句")
    parser.add_argument("--lessons", help="课号范围: 1-5, 1,3,5, 7")
    parser.add_argument("--dry-run", action="store_true", help="预览不写入")
    args = parser.parse_args()

    lesson_range = parse_lesson_range(args.lessons) if args.lessons else None

    if not wait(5):
        print("✗ 请打开 Anki")
        return

    print("Loading example data...")
    examples = load_examples(lesson_range)
    if not examples:
        print("✗ 没有找到例句数据，请先在 anki/examples/ 目录放入 lesson_XX.json")
        return
    print(f"  Total: {len(examples)} entries\n")

    for profile in PROFILES:
        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(10)
        if not wait():
            print(f"  ✗ {profile} 超时")
            continue
        # Sanity check: verify profile actually switched
        nids_check = anki("findNotes", query=f'"deck:{DECK}"')
        print(f"  {profile}: {len(nids_check)} notes")
        updated, skipped, missing = fill_profile(examples, dry_run=args.dry_run)
        print(f"  ✓ {profile}: {updated} 填入, {skipped} 跳过(已有), {missing} 未匹配")

    # Switch back
    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)
    prefix = "[dry-run] " if args.dry_run else ""
    print(f"\n{prefix}✅ 例句填充完成")


if __name__ == "__main__":
    main()
