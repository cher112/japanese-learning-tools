#!/usr/bin/env python3
"""
解锁「中文→日文」卡片
只解锁那些「日文→含义」方向已复习 ≥ N 次的词
"""
import json
import urllib.request
import os
import sys

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
DECK = "みんなの日本語初级1-2 単語"
MIN_REVIEWS = 3  # 日文→含义 复习 ≥ 3 次后解锁中文→日文


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


def main():
    threshold = MIN_REVIEWS
    if len(sys.argv) > 1:
        try:
            threshold = int(sys.argv[1])
        except ValueError:
            pass

    print(f"解锁条件: 日文→含义 已复习 ≥ {threshold} 次")
    print("-" * 40)

    try:
        anki("version")
    except Exception:
        print("✗ 请打开 Anki")
        return

    # 获取所有「日文→含义」卡片 (card:1 = 第一个模板)
    jp_cards = anki("findCards", query=f'"deck:{DECK}" card:1')
    if not jp_cards:
        print("未找到卡片")
        return

    jp_info = anki("cardsInfo", cards=jp_cards)

    # 找出复习次数 >= threshold 的 note IDs
    ready_notes = set()
    for card in jp_info:
        if card["reps"] >= threshold:
            ready_notes.add(card["note"])

    print(f"日文→含义 总卡片: {len(jp_cards)}")
    print(f"已复习 ≥{threshold} 次: {len(ready_notes)} 个词")

    if not ready_notes:
        print("\n暂无可解锁的卡片，继续复习吧！")
        return

    # 获取所有已挂起的「中文→日文」卡片 (card:2 = 第二个模板)
    cn_cards = anki("findCards", query=f'"deck:{DECK}" card:2 is:suspended')
    if not cn_cards:
        print("\n没有已挂起的中文→日文卡片")
        return

    cn_info = anki("cardsInfo", cards=cn_cards)

    # 找出对应的挂起卡片
    to_unsuspend = []
    for card in cn_info:
        if card["note"] in ready_notes:
            to_unsuspend.append(card["cardId"])

    if not to_unsuspend:
        print("\n所有符合条件的中文→日文卡片已解锁")
        return

    anki("unsuspend", cards=to_unsuspend)
    print(f"\n✅ 解锁了 {len(to_unsuspend)} 张「中文→日文」卡片！")

    # 统计剩余挂起
    remaining = len(cn_cards) - len(to_unsuspend)
    print(f"剩余挂起: {remaining} 张")


if __name__ == "__main__":
    main()
