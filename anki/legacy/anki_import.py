#!/usr/bin/env python3
"""
从 単語補充.md 解析生词表，通过 AnkiConnect 导入 Anki。
用法: python3 anki_import.py
要求: Anki 已打开且安装了 AnkiConnect 插件（代码 2055492159）
"""

import json
import re
import urllib.request

ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = "日语N5单词"
MODEL_NAME = "日语单词卡片"

MD_FILE = "単語補充.md"


def anki_request(action, **params):
    """发送请求到 AnkiConnect"""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode("utf-8"))
    if result.get("error"):
        raise Exception(f"AnkiConnect error: {result['error']}")
    return result.get("result")


def ensure_deck():
    """确保牌组存在"""
    anki_request("createDeck", deck=DECK_NAME)
    print(f"✓ 牌组 '{DECK_NAME}' 已就绪")


def ensure_model():
    """确保卡片模板存在"""
    models = anki_request("modelNames")
    if MODEL_NAME in models:
        print(f"✓ 模板 '{MODEL_NAME}' 已存在")
        return

    anki_request(
        "createModel",
        modelName=MODEL_NAME,
        inOrderFields=["日语", "读音", "中文", "词性", "例句", "课"],
        css="""
.card { font-family: "Hiragino Sans", "Yu Gothic", sans-serif; font-size: 24px;
        text-align: center; color: #333; background: #fafafa; padding: 20px; }
.word { font-size: 36px; font-weight: bold; color: #1a1a2e; margin: 10px 0; }
.reading { font-size: 20px; color: #e94560; margin: 5px 0; }
.meaning { font-size: 22px; color: #0f3460; margin: 10px 0; }
.pos { font-size: 14px; color: #888; }
.example { font-size: 16px; color: #555; margin-top: 15px;
           border-top: 1px solid #ddd; padding-top: 10px; text-align: left; }
.lesson { font-size: 12px; color: #aaa; margin-top: 10px; }
""",
        cardTemplates=[
            {
                "Name": "日→中",
                "Front": '<div class="word">{{日语}}</div><div class="pos">{{词性}}</div>',
                "Back": """
<div class="word">{{日语}}</div>
<div class="reading">{{读音}}</div>
<div class="meaning">{{中文}}</div>
<div class="pos">{{词性}}</div>
<div class="example">{{例句}}</div>
<div class="lesson">{{课}}</div>
""",
            },
            {
                "Name": "中→日",
                "Front": '<div class="meaning">{{中文}}</div><div class="pos">{{词性}}</div>',
                "Back": """
<div class="word">{{日语}}</div>
<div class="reading">{{读音}}</div>
<div class="meaning">{{中文}}</div>
<div class="pos">{{词性}}</div>
<div class="example">{{例句}}</div>
<div class="lesson">{{课}}</div>
""",
            },
        ],
    )
    print(f"✓ 模板 '{MODEL_NAME}' 已创建（日→中 / 中→日 双向卡片）")


def parse_md(filepath):
    """解析 単語補充.md 中的表格，提取单词"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    words = []
    current_lesson = ""
    current_pos = ""

    for line in content.split("\n"):
        # 匹配课号: ## 第18课单词
        m = re.match(r"^##\s+(第\d+课\S*|.*改错.*|同音異義語.*)", line)
        if m:
            current_lesson = m.group(1).strip()
            continue

        # 匹配词性: ### 名词 / ### 动词 等
        m = re.match(r"^###\s+(.+)", line)
        if m:
            current_pos = m.group(1).strip()
            continue

        # 跳过非表格行和表头分隔符
        if not line.startswith("|") or line.startswith("|--") or line.startswith("| 日语") or line.startswith("| 题目") or line.startswith("| 读音") or line.startswith("| 词汇"):
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]

        if not cells or len(cells) < 3:
            continue

        # 跳过数字读法练习和同音异义词部分
        if "改错" in current_lesson or "同音異義語" in current_lesson:
            continue

        # 根据列数判断格式
        if current_pos == "动词" and len(cells) >= 5:
            word = {
                "日语": cells[0],
                "读音": cells[1] if cells[1] != "-" else "",
                "中文": cells[2],
                "词性": current_pos,
                "例句": cells[4] if len(cells) > 4 else "",
                "课": current_lesson,
            }
        elif current_pos == "副词" and len(cells) >= 5:
            word = {
                "日语": cells[0],
                "读音": cells[1] if cells[1] != "-" else "",
                "中文": cells[2],
                "词性": current_pos,
                "例句": cells[4] if len(cells) > 4 else "",
                "课": current_lesson,
            }
        elif len(cells) >= 4:
            word = {
                "日语": cells[0],
                "读音": cells[1] if cells[1] != "-" else "",
                "中文": cells[2],
                "词性": current_pos,
                "例句": cells[3] if len(cells) > 3 else "",
                "课": current_lesson,
            }
        else:
            word = {
                "日语": cells[0],
                "读音": cells[1] if len(cells) > 1 and cells[1] != "-" else "",
                "中文": cells[2] if len(cells) > 2 else "",
                "词性": current_pos,
                "例句": "",
                "课": current_lesson,
            }

        # 清理 HTML/markdown 标记
        for k in word:
            word[k] = word[k].replace("<br>", "\n")

        if word["日语"]:
            words.append(word)

    return words


def import_words(words):
    """批量导入单词到 Anki"""
    notes = []
    for w in words:
        notes.append(
            {
                "deckName": DECK_NAME,
                "modelName": MODEL_NAME,
                "fields": w,
                "options": {"allowDuplicate": False},
                "tags": [f"lesson:{w['课']}", w["词性"]] if w["课"] else [w["词性"]],
            }
        )

    result = anki_request("addNotes", notes=notes)
    added = sum(1 for r in result if r is not None)
    skipped = sum(1 for r in result if r is None)
    print(f"✓ 导入完成: {added} 张新卡片, {skipped} 张跳过（已存在）")
    return added, skipped


def main():
    print("=" * 40)
    print("  Anki 日语生词导入工具")
    print("=" * 40)

    # 测试连接
    try:
        anki_request("version")
        print("✓ AnkiConnect 连接成功")
    except Exception:
        print("✗ 无法连接 AnkiConnect！")
        print("  请确保：1) Anki 已打开  2) AnkiConnect 插件已安装（代码 2055492159）")
        return

    ensure_deck()
    ensure_model()

    words = parse_md(MD_FILE)
    print(f"✓ 从 {MD_FILE} 解析出 {len(words)} 个单词")

    if words:
        # 预览前3个
        print("\n预览前3个:")
        for w in words[:3]:
            print(f"  {w['日语']}（{w['读音']}）- {w['中文']} [{w['词性']}]")
        print()

        import_words(words)

    print("\n完成！打开 Anki 查看牌组「日语N5单词」")


if __name__ == "__main__":
    main()
