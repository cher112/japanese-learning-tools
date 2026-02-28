#!/usr/bin/env python3
"""
生成 grammar_quiz.json 模板（需手工审核/编辑）

每个语法点生成 1 道选择题，格式：
{
  "id": "L1-1",
  "lesson": "第1課",
  "title": "名詞1は 名詞2です",
  "question": "わたし ___ 会社員です。",
  "options": ["は", "が", "を", "に"],
  "answer": "は",
  "hint": "助詞「は」表示主題"
}

用法：
  python3 generate_grammar_quiz.py          # 生成初始模板
  python3 generate_grammar_quiz.py --check  # 检查已有 quiz JSON 完整性
"""
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(DIR, "grammar", "grammar_data.json")
QUIZ = os.path.join(DIR, "grammar", "grammar_quiz.json")


def generate_template():
    """生成空白模板，每个语法点 1 题，需手工填写"""
    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)

    quizzes = []
    for item in data:
        ex1_jp = item["examples"][0]["jp"] if item["examples"] else ""
        quizzes.append({
            "id": item["id"],
            "lesson": item["lesson"],
            "title": item["title"],
            "question": "",       # 填入题干（含 ___ 空位）
            "options": ["", "", "", ""],  # 4 个选项
            "answer": "",         # 正确答案（必须是 options 之一）
            "hint": "",           # 翻面解说
            "_ref_example": ex1_jp,  # 参考例句（不导入，仅供出题参考）
        })

    os.makedirs(os.path.dirname(QUIZ), exist_ok=True)
    with open(QUIZ, "w", encoding="utf-8") as f:
        json.dump(quizzes, f, ensure_ascii=False, indent=2)

    print(f"✅ 模板已生成: {len(quizzes)} 题 → {QUIZ}")
    print("   请手工编辑 question / options / answer / hint")
    print("   编辑完成后运行 --check 检查完整性")


def check():
    """检查 quiz JSON 完整性"""
    with open(QUIZ, "r", encoding="utf-8") as f:
        quizzes = json.load(f)

    errors = []
    filled = 0
    for q in quizzes:
        qid = q["id"]
        if not q["question"]:
            errors.append(f"  {qid}: question 为空")
            continue
        if len(q["options"]) != 4:
            errors.append(f"  {qid}: options 不是 4 个")
            continue
        if any(not o for o in q["options"]):
            errors.append(f"  {qid}: 有空白选项")
            continue
        if not q["answer"]:
            errors.append(f"  {qid}: answer 为空")
            continue
        if q["answer"] not in q["options"]:
            errors.append(f"  {qid}: answer「{q['answer']}」不在 options 中")
            continue
        filled += 1

    print(f"总计: {len(quizzes)} 题")
    print(f"已完成: {filled}")
    print(f"未完成/有错: {len(errors)}")
    if errors:
        print("\n问题列表:")
        for e in errors[:20]:
            print(e)
        if len(errors) > 20:
            print(f"  ... 还有 {len(errors) - 20} 个")
    else:
        print("✅ 全部通过！可以导入 Anki")


def main():
    if "--check" in sys.argv:
        check()
    else:
        if os.path.exists(QUIZ):
            print(f"⚠ {QUIZ} 已存在，跳过生成")
            print("  删除后重新运行，或直接编辑现有文件")
            print("  用 --check 检查完整性")
            return
        generate_template()


if __name__ == "__main__":
    main()
