#!/usr/bin/env python3
"""解析 初级1/文法.md → grammar_data.json"""
import json
import re
import os

GRAMMAR_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "初级1", "文法.md")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "grammar", "grammar_data.json")


def parse():
    with open(GRAMMAR_MD, "r", encoding="utf-8") as f:
        text = f.read()

    results = []
    current_lesson = ""

    # Split into lines for processing
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect lesson heading: ## 第N課
        m = re.match(r"^## 第(\d+)課", line)
        if m:
            current_lesson = f"第{m.group(1)}課"
            i += 1
            continue

        # Detect grammar point: ### N. title
        m = re.match(r"^### (\d+)\. (.+)$", line)
        if m:
            number = int(m.group(1))
            title = m.group(2).strip()

            # Collect everything until next ### or ## or end
            i += 1
            body_lines = []
            while i < len(lines):
                if re.match(r"^###? ", lines[i]) or re.match(r"^---", lines[i]):
                    break
                body_lines.append(lines[i])
                i += 1

            body = "\n".join(body_lines)

            # Extract examples: lines starting with circled numbers ①②③...
            # Pattern: ① Japanese text（Chinese text）
            examples = []
            circle_nums = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
            for bline in body_lines:
                bline = bline.strip()
                if not bline:
                    continue
                # Check if line starts with a circled number
                if bline and bline[0] in circle_nums:
                    # Extract JP and CN parts
                    # Format: ① JP text（CN text）
                    content = bline[1:].strip()
                    # Find Chinese in （...）
                    cn_match = re.search(r"（(.+?)）\s*$", content)
                    if cn_match:
                        cn = cn_match.group(1)
                        jp = content[:cn_match.start()].strip()
                    else:
                        jp = content
                        cn = ""
                    examples.append({"jp": jp, "cn": cn})

            # Build explanation: non-example, non-empty lines
            explanation_lines = []
            for bline in body_lines:
                stripped = bline.strip()
                if not stripped:
                    continue
                # Skip example lines (circled numbers)
                if stripped and stripped[0] in circle_nums:
                    continue
                # Skip response lines starting with ……
                if stripped.startswith("……"):
                    continue
                # Skip table lines
                if stripped.startswith("|") or stripped.startswith("---"):
                    continue
                # Skip [注] lines (include them actually - they're useful)
                # Skip × lines (wrong usage examples)
                if stripped.startswith("×"):
                    continue
                explanation_lines.append(stripped)

            explanation = "\n".join(explanation_lines)

            # Build global ID
            global_id = f"L{current_lesson[1:-1].replace('第','').replace('課','')}-{number}"

            results.append({
                "id": global_id,
                "lesson": current_lesson,
                "lesson_num": int(re.search(r"\d+", current_lesson).group()),
                "number": number,
                "title": title,
                "explanation": explanation,
                "examples": examples,
            })
            continue

        i += 1

    return results


def main():
    data = parse()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Summary
    lessons = {}
    for item in data:
        l = item["lesson"]
        lessons[l] = lessons.get(l, 0) + 1

    print(f"✅ 解析完成: {len(data)} 个语法点")
    total_ex = sum(len(item["examples"]) for item in data)
    print(f"   例句总数: {total_ex}")
    print(f"   课数: {len(lessons)}")
    for l in sorted(lessons, key=lambda x: int(re.search(r"\d+", x).group())):
        print(f"   {l}: {lessons[l]} 个语法点")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
