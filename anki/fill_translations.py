#!/usr/bin/env python3
"""一次性脚本：为補充単語填入例句中文翻译"""
import json
import urllib.request
import os
import re
import time

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
PROFILES = ["szmz", "czh"]

TRANSLATIONS = {
    "弄びます": "猫在玩弄玩具。",
    "お年玉": "过年时从爷爷那里收到了红包。",
    "黙ります": "老师来了，大家都沉默了。",
    "許します": "朋友道歉了，所以我原谅了他。",
    "突き止めます": "必须查清原因。",
    "裏切ります": "不能背叛朋友。",
    "裏切り者": "那个人被说是背叛者。",
    "お小遣い": "每个月都会收到零花钱。",
    "落ち着きます": "请先冷静下来，没事的。",
    "係の人": "请问前台的工作人员。",
    "趣味": "你的爱好是什么？——是弹吉他。",
    "日記": "每天都在写日记。",
    "ギター": "每晚都在练习吉他。",
    "歌": "我非常喜欢这首歌。",
    "係長": "请向科长汇报。",
    "そば": "车站旁边有便利店。",
    "壁": "在墙上贴了照片。",
    "裏": "建筑物后面有停车场。",
    "北": "北边比较冷。",
    "弾きます": "姐姐钢琴弹得很好。",
    "歌います": "在KTV唱了日语歌。",
    "集めます": "集邮是我的爱好。",
    "捨てます": "不要的东西请扔掉。",
    "払います": "可以刷卡吗？",
    "見学します": "参观了工厂。",
    "入場します": "没有票不能入场。",
    "利用します": "这项服务可以免费使用。",
    "注文します": "不好意思，我想点拉面。",
    "並べます": "在桌子上摆好了书。",
    "置きます": "请把包放在这里。",
    "泊まります": "在京都的酒店住了两晚。",
    "安い": "这家店又便宜又好吃。",
    "にぎやか": "涩谷总是很热闹。",
    "特に": "日本料理中，我特别喜欢寿司。",
    "もうすぐ": "马上就要放暑假了，好期待。",
    "どんな": "你喜欢什么样的音乐？",
    "ほんとうですか": "下个月去日本。——真的吗！",
    "おいくら": "请问这个多少钱？",
    "階段": "请走楼梯上到3楼。",
    "山": "周末和朋友去爬山了。",
    "勧める": "向朋友推荐了这本书。",
    "進める": "推进计划吧。",
    "薦める": "老师推荐了这位学生。",
}


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
    return re.sub(r" ?(\S+)\[([^\]]+)\]", r"\1", text).strip()


def fill_profile():
    nids = anki("findNotes", query="deck:補充単語")
    if not nids:
        return 0
    infos = anki("notesInfo", notes=nids)
    count = 0
    for n in infos:
        jp_raw = n["fields"]["日文"]["value"]
        clean = strip_furigana(jp_raw)
        trans = TRANSLATIONS.get(clean, "")
        if not trans:
            continue
        existing = n["fields"].get("例句翻译", {}).get("value", "")
        if existing:
            continue
        anki("updateNoteFields", note={
            "id": n["noteId"],
            "fields": {"例句翻译": trans}
        })
        count += 1
    return count


def main():
    if not wait(5):
        print("✗ 请打开 Anki")
        return
    for profile in PROFILES:
        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(5)
        if not wait():
            print(f"  ✗ {profile} 超时")
            continue
        count = fill_profile()
        print(f"  ✓ {profile}: {count} 个翻译已填入")
    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)
    print("✅ 例句翻译填充完成")


if __name__ == "__main__":
    main()
