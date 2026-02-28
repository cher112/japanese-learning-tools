#!/usr/bin/env python3
"""一次性脚本：为補充単語的43个词填入例句（两个Profile）"""
import json
import urllib.request
import os
import time

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
PROFILES = ["szmz", "czh"]

# 手写的 N5 水平例句，自然、实用
EXAMPLES = {
    "弄びます": "猫がおもちゃを 弄[もてあそ]んでいます。",
    "お年玉": "お 正月[しょうがつ]に おじいちゃんから お 年玉[としだま]を もらいました。",
    "黙ります": " 先生[せんせい]が 来[き]たら、みんな 黙[だま]りました。",
    "許します": "友だちが 謝[あやま]ったので、 許[ゆる]しました。",
    "突き止めます": " 原因[げんいん]を 突[つ]き 止[と]めなければなりません。",
    "裏切ります": " 友[とも]だちを 裏切[うらぎ]ってはいけません。",
    "裏切り者": "あの 人[ひと]は 裏切[うらぎ]り 者[もの]だと 言[い]われています。",
    "お小遣い": " 毎月[まいつき] お 小遣[こづか]いを もらっています。",
    "落ち着きます": "まず 落[お]ち 着[つ]いてください。 大丈夫[だいじょうぶ]ですよ。",
    "係の人": " 受付[うけつけ]の 係[かかり]の 人[ひと]に 聞[き]いてください。",
    "趣味": " 趣味[しゅみ]は 何[なん]ですか。——ギターを 弾[ひ]くことです。",
    "日記": " 毎日[まいにち] 日記[にっき]を 書[か]いています。",
    "ギター": " 毎晩[まいばん] ギターを 練習[れんしゅう]しています。",
    "歌": "この 歌[うた]が 大好[だいす]きです。",
    "係長": " 係長[かかりちょう]に 報告[ほうこく]してください。",
    "そば": " 駅[えき]の そばに コンビニがあります。",
    "壁": " 壁[かべ]に 写真[しゃしん]を 貼[は]りました。",
    "裏": " 建物[たてもの]の 裏[うら]に 駐車場[ちゅうしゃじょう]があります。",
    "北": " 北[きた]の 方[ほう]は 寒[さむ]いです。",
    "弾きます": " 姉[あね]は ピアノを 上手[じょうず]に 弾[ひ]きます。",
    "歌います": "カラオケで 日本[にほん]の 歌[うた]を 歌[うた]いました。",
    "集めます": " 切手[きって]を 集[あつ]めるのが 趣味[しゅみ]です。",
    "捨てます": "いらない 物[もの]は 捨[す]ててください。",
    "払います": "カードで 払[はら]ってもいいですか。",
    "見学します": " 工場[こうじょう]を 見学[けんがく]しました。",
    "入場します": "チケットがないと 入場[にゅうじょう]できません。",
    "利用します": "この サービスは 無料[むりょう]で 利用[りよう]できます。",
    "注文します": "すみません、ラーメンを 注文[ちゅうもん]したいんですが。",
    "並べます": " 机[つくえ]の 上[うえ]に 本[ほん]を 並[なら]べました。",
    "置きます": "かばんを ここに 置[お]いてください。",
    "泊まります": " 京都[きょうと]の ホテルに 二泊[にはく] 泊[と]まりました。",
    "安い": "この 店[みせ]は 安[やす]くて おいしいです。",
    "にぎやか": " 渋谷[しぶや]は いつも にぎやかです。",
    "特に": " 日本料理[にほんりょうり]の 中[なか]で、 特[とく]に すしが 好[す]きです。",
    "もうすぐ": "もうすぐ 夏休[なつやす]みです。 楽[たの]しみですね。",
    "どんな": "どんな 音楽[おんがく]が 好[す]きですか。",
    "ほんとうですか": "来月[らいげつ] 日本[にほん]に 行[い]きます。——ほんとうですか！",
    "おいくら": "すみません、これは おいくらですか。",
    "階段": " 階段[かいだん]で ３ 階[かい]まで 上[あ]がってください。",
    "山": " 週末[しゅうまつ] 友[とも]だちと 山[やま]に 登[のぼ]りました。",
    "勧める": " 友[とも]だちに この 本[ほん]を 勧[すす]めました。",
    "進める": " 計画[けいかく]を 進[すす]めましょう。",
    "薦める": " 先生[せんせい]が この 学生[がくせい]を 薦[すす]めました。",
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


def fill_profile():
    nids = anki("findNotes", query="deck:補充単語")
    if not nids:
        return 0
    infos = anki("notesInfo", notes=nids)
    updated = 0
    for n in infos:
        jp_raw = n["fields"]["日文"]["value"]
        # Strip furigana markup to match keys
        import re
        clean = re.sub(r" ?(\S+)\[([^\]]+)\]", r"\1", jp_raw)
        ex = EXAMPLES.get(clean, "")
        if not ex:
            continue
        existing = n["fields"].get("例句", {}).get("value", "")
        if existing:
            continue
        anki("updateNoteFields", note={
            "id": n["noteId"],
            "fields": {"例句": ex}
        })
        updated += 1
    return updated


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
        print(f"  ✓ {profile}: {count} 个例句已填入")

    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)
    print("✅ 例句填充完成")


if __name__ == "__main__":
    main()
