#!/usr/bin/env python3
"""
从初级1和初级2的 output.md 提取每课单词，生成干净的 单词.md
并通过 AnkiConnect 导入 Anki。
"""

import re
import json
import urllib.request
import base64
import time
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = "初级1-2"
MODEL_NAME = "日语单词卡片"

TTS_API_URL = "https://www.dmxapi.cn/v1/audio/speech"
TTS_API_KEY = "sk-xSnH2iKopoiPDZp78UBSDTHi4iugbv3VbXT3NlanJ8A3RF8t"
TTS_MODEL = "speech-2.6-hd"
TTS_VOICE = "female-shaonv"


def anki_request(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(
        ANKI_CONNECT_URL, data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode("utf-8"))
    err = result.get("error")
    # addNotes 返回 error 为 list（每个 note 的状态），不算整体错误
    if err and isinstance(err, str):
        raise Exception(f"AnkiConnect: {err}")
    return result.get("result")


def generate_tts(text):
    payload = json.dumps({"model": TTS_MODEL, "voice": TTS_VOICE, "input": text})
    req = urllib.request.Request(
        TTS_API_URL, data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {TTS_API_KEY}"},
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return base64.b64encode(resp.read()).decode("utf-8")


def clean_html(text):
    """清理 HTML 实体和标签"""
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def extract_reading_and_kanji(raw_word):
    """从 OCR 词条中提取读音和汉字写法"""
    raw = raw_word.strip()
    # 去除标记符号
    raw = re.sub(r"^[▲△★●■□◆※]", "", raw)
    # 去除末尾声调数字 ①②③④⑤⑥⑦⑧⑨⑩ 或 $①$ 等
    raw = re.sub(r"\$?[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]\$?$", "", raw).strip()
    raw = re.sub(r"\s*[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]\s*$", "", raw).strip()

    # 提取括号中的汉字：ひらがな(漢字)
    m = re.match(r"^(.+?)\s*[(\（](.+?)[)\）]\s*$", raw)
    if m:
        part1, part2 = m.group(1).strip(), m.group(2).strip()
        # 判断哪个是假名哪个是汉字
        if re.search(r"[ぁ-んァ-ヶ]", part1):
            return part1, part2  # reading, kanji
        return part2, part1  # reading, kanji

    # 提取动词辞书形：待ちます(←待つ)
    m = re.match(r"^(.+?)\s*[(\（]\s*←\s*(.+?)\s*[)\）]\s*$", raw)
    if m:
        masu = m.group(1).strip()
        jisho = m.group(2).strip()
        return masu, jisho

    return raw, ""


def parse_pos(raw_pos):
    """解析词性标签"""
    pos = clean_html(raw_pos)
    pos = re.sub(r"[<>〈〉\(\)]", "", pos).strip()
    pos_map = {
        "名": "名词", "動I": "动词I", "動II": "动词II", "動Ⅱ": "动词II",
        "動III": "动词III", "動Ⅲ": "动词III", "形": "い形容词", "形動": "な形容词",
        "副": "副词", "感": "感叹词", "接尾": "接尾词", "連語": "连语",
        "助数": "量词", "接辞": "接辞", "接": "接续词", "造語": "造语",
        "数": "数词", "疑": "疑问词",
    }
    return pos_map.get(pos, pos) if pos else ""


def parse_tables_from_content(content, book_label):
    """从 output.md 解析所有单词表"""
    all_words = []

    # 找到每课的位置: # 第X课 或 类似标记
    # 先把内容按 单語/単語 section 切分
    # 找所有 単語 section 的位置
    section_pattern = re.compile(r"^#+\s*(?:单語|単語)", re.MULTILINE)
    section_starts = [m.start() for m in section_pattern.finditer(content)]

    if not section_starts:
        return all_words

    # 找每个 section 前面最近的课号
    lesson_pattern = re.compile(r"(?:^|\n)#+\s*第\s*(\d+)\s*课")

    for sec_idx, sec_start in enumerate(section_starts):
        # 找这个 section 之前最近的课号
        lesson_num = None
        for m in lesson_pattern.finditer(content[:sec_start]):
            lesson_num = int(m.group(1))

        if lesson_num is None:
            lesson_num = sec_idx + 1

        lesson_label = f"{book_label} 第{lesson_num}课"

        # 这个 section 到下一个 section 的内容
        sec_end = section_starts[sec_idx + 1] if sec_idx + 1 < len(section_starts) else sec_start + 5000
        section = content[sec_start:sec_end]

        # 在 section 中找 3 列 table
        tables = re.findall(r"<table>(.*?)</table>", section, re.DOTALL)
        for table in tables:
            rows = re.findall(r"<tr>(.*?)</tr>", table, re.DOTALL)
            for row in rows:
                cells = [clean_html(c) for c in re.findall(r"<td>(.*?)</td>", row, re.DOTALL)]
                if len(cells) < 3:
                    continue

                raw_word, raw_pos, meaning = cells[0].strip(), cells[1].strip(), cells[2].strip()
                if not raw_word or not meaning:
                    continue
                # 跳过表头
                if raw_word in ("", "ます形", "て形", "ない形", "辞書形"):
                    continue

                word, extra = extract_reading_and_kanji(raw_word)
                pos = parse_pos(raw_pos)

                # 跳过例句行（通常没有词性）
                if not pos and len(word) > 8:
                    continue

                all_words.append({
                    "日语": word,
                    "读音": extra if extra else "",
                    "中文": meaning,
                    "词性": pos,
                    "课": lesson_label,
                })

        # 如果没找到 table，尝试解析内联格式
        if not tables:
            # 格式: word <POS> meaning 在同一行
            inline_pattern = re.compile(
                r"^(.+?)\s*[<〈\(]([名動形副感接連助疑数造][^>〉\)]*)[>〉\)]\s*(.+)$",
                re.MULTILINE,
            )
            for m in inline_pattern.finditer(section):
                raw_word = m.group(1).strip()
                raw_pos = m.group(2).strip()
                meaning = m.group(3).strip()

                if not raw_word or not meaning:
                    continue

                word, extra = extract_reading_and_kanji(raw_word)
                pos = parse_pos(f"<{raw_pos}>")

                all_words.append({
                    "日语": word,
                    "读音": extra if extra else "",
                    "中文": meaning,
                    "词性": pos,
                    "课": lesson_label,
                })

    return all_words


def generate_markdown(words_by_lesson):
    """生成 单词.md"""
    lines = ["# 初级1-2 单词表\n"]
    total = 0

    for lesson, words in sorted(words_by_lesson.items()):
        lines.append(f"\n## {lesson}\n")
        lines.append("| 日语 | 读音 | 词性 | 中文 |")
        lines.append("|------|------|------|------|")
        for w in words:
            lines.append(f"| {w['日语']} | {w['读音']} | {w['词性']} | {w['中文']} |")
            total += 1

    lines.append(f"\n---\n共 {total} 个单词\n")
    return "\n".join(lines), total


def main():
    print("=" * 50)
    print("  初级1-2 单词提取 → 单词.md → Anki 导入")
    print("=" * 50)

    # ---- Step 1: 解析 ----
    all_words = []
    for book, folder in [("初级1", "初级1"), ("初级2", "初级2")]:
        filepath = os.path.join(BASE_DIR, folder, "output.md")
        if not os.path.exists(filepath):
            print(f"✗ 文件不存在: {filepath}")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        words = parse_tables_from_content(content, book)
        print(f"✓ {book}: 解析出 {len(words)} 个词条")
        all_words.extend(words)

    if not all_words:
        print("✗ 没有解析出任何单词")
        return

    # 按课分组
    words_by_lesson = {}
    for w in all_words:
        lesson = w["课"]
        if lesson not in words_by_lesson:
            words_by_lesson[lesson] = []
        words_by_lesson[lesson].append(w)

    # ---- Step 2: 生成 单词.md ----
    md_content, total = generate_markdown(words_by_lesson)
    md_path = os.path.join(BASE_DIR, "单词.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n✓ 已生成 单词.md（{total} 个单词，{len(words_by_lesson)} 课）")

    # ---- Step 3: 导入 Anki ----
    try:
        anki_request("version")
        print("✓ AnkiConnect 连接成功")
    except Exception:
        print("✗ AnkiConnect 未连接，跳过 Anki 导入")
        print("  单词.md 已生成，可稍后手动导入")
        return

    # 创建牌组
    anki_request("createDeck", deck=DECK_NAME)
    print(f"✓ 牌组「{DECK_NAME}」已就绪")

    # 确保音声字段存在
    fields = anki_request("modelFieldNames", modelName=MODEL_NAME)
    if "音声" not in fields:
        anki_request("modelFieldAdd", modelName=MODEL_NAME, fieldName="音声", index=6)

    # 批量创建卡片（过滤空词条）
    notes = []
    for w in all_words:
        if not w["日语"].strip():
            continue
        notes.append({
            "deckName": DECK_NAME,
            "modelName": MODEL_NAME,
            "fields": {
                "日语": w["日语"],
                "读音": w["读音"],
                "中文": w["中文"],
                "词性": w["词性"],
                "例句": "",
                "课": w["课"],
                "音声": "",
            },
            "options": {"allowDuplicate": False},
            "tags": [w["课"].replace(" ", "_"), w["词性"]] if w["词性"] else [w["课"].replace(" ", "_")],
        })

    # 用 canAddNotesWithErrorDetail 替代 addNotes，逐条导入避免整体失败
    added = 0
    skipped = 0
    for w_note in notes:
        try:
            ids = anki_request("addNotes", notes=[w_note])
            if ids and ids[0]:
                added += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1
    print(f"✓ Anki 导入: {added} 张新卡片, {skipped} 张跳过")

    # ---- Step 4: TTS 语音 ----
    print(f"\n正在生成 TTS 语音（{added} 张新卡片）...")
    note_ids = anki_request("findNotes", query=f'"deck:{DECK_NAME}"')
    notes_info = anki_request("notesInfo", notes=note_ids)

    generated = 0
    failed = 0
    for i, note in enumerate(notes_info):
        fields = note["fields"]
        word = fields["日语"]["value"]
        reading = fields.get("读音", {}).get("value", "")
        audio = fields.get("音声", {}).get("value", "")

        if audio and "[sound:" in audio:
            continue

        tts_text = reading if reading else word
        if not tts_text or len(tts_text) > 30:
            continue

        filename = f"jp_tts_{word.replace('/', '_')}.mp3"

        sys.stdout.write(f"\r  [{i+1}/{len(notes_info)}] {word}...")
        sys.stdout.flush()

        try:
            audio_b64 = generate_tts(tts_text)
            anki_request("storeMediaFile", filename=filename, data=audio_b64)
            anki_request("updateNoteFields", note={
                "id": note["noteId"],
                "fields": {"音声": f"[sound:{filename}]"},
            })
            generated += 1
            time.sleep(0.3)
        except Exception as e:
            failed += 1
            continue

    print(f"\n✓ TTS: {generated} 条生成, {failed} 条失败")
    print(f"\n✅ 全部完成！牌组「{DECK_NAME}」已就绪")


if __name__ == "__main__":
    main()
