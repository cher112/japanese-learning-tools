#!/usr/bin/env python3
"""
从 /tmp/anki_all_words.json 读取词表，自动生成 lesson_09~50.json 例句文件。
根据词性和中文意思生成 N5 水平的自然例句。
"""
import json
import re
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "examples")

def load_words():
    with open("/tmp/anki_all_words.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ── 按词性生成例句的模板 ──────────────────────────────

def make_sentence(key, raw, pos, cn):
    """Generate (jp_sentence, cn_sentence) for a word."""

    # ── 固定短语 / 寒暄语（key 以。结尾或含 ～） ──
    if key.endswith("。") or key.endswith("……"):
        return _phrase(key, raw, cn)
    if key.startswith("～") or key.startswith("―"):
        return _pattern(key, raw, cn)

    # ── 动词 ──
    if "動" in pos:
        return _verb(key, raw, cn)
    # ── い形容词 ──
    if "イ形" in pos or pos == "形":
        return _i_adj(key, raw, cn)
    # ── な形容词 ──
    if "ナ形" in pos:
        return _na_adj(key, raw, cn)
    # ── 副词 ──
    if "副" in pos:
        return _adverb(key, raw, cn)
    # ── 感叹词 ──
    if "感" in pos:
        return _interj(key, raw, cn)
    # ── 接续词 ──
    if "接" in pos and "接尾" not in pos:
        return _conj(key, raw, cn)
    # ── 名词（默认） ──
    return _noun(key, raw, cn)


def _use_raw(raw):
    """Convert raw furigana to sentence-usable form."""
    # raw is already in Anki furigana format
    return raw


def _phrase(key, raw, cn):
    """Fixed phrases - wrap in context."""
    # Use the raw form directly as the example
    jp = raw.rstrip("。") + "。" if not raw.endswith("。") else raw
    return jp, cn.rstrip("。") + "。" if cn else cn


def _pattern(key, raw, cn):
    """Grammar patterns like ～より, ―枚."""
    jp = raw
    return jp, cn


def _verb(key, raw, cn):
    """Generate verb example."""
    r = _use_raw(raw)
    # Extract the clean verb for matching
    cn_clean = cn.split("、")[0].split("（")[0].strip()

    # Common verb patterns based on Chinese meaning
    patterns = {
        "吃": (f" 朝[あさ]ごはんを{r}。", f"吃早饭。"),
        "喝": (f" 毎朝[まいあさ] コーヒーを{r}。", f"每天早上喝咖啡。"),
        "看": (f" 映画[えいが]を{r}。", f"看电影。"),
        "听": (f" 音楽[おんがく]を{r}。", f"听音乐。"),
        "读": (f" 本[ほん]を{r}。", f"看书。"),
        "写": (f" 手紙[てがみ]を{r}。", f"写信。"),
        "买": (f"デパートで{r}。", f"在百货商店买。"),
        "去": (f" 学校[がっこう]へ{r}。", f"去学校。"),
        "来": (f" 日本[にほん]へ{r}。", f"来日本。"),
        "做": (f" 毎日[まいにち] 宿題[しゅくだい]を{r}。", f"每天做作业。"),
        "学": (f" 日本語[にほんご]を{r}。", f"学日语。"),
        "教": (f" 日本語[にほんご]を{r}。", f"教日语。"),
        "工作": (f" 毎日[まいにち]{r}。", f"每天工作。"),
        "休息": (f" 日曜日[にちようび]は{r}。", f"周日休息。"),
        "睡": (f" 毎晩[まいばん] 11 時[じ]に{r}。", f"每天晚上11点睡觉。"),
        "起": (f" 毎朝[まいあさ] 7 時[じ]に{r}。", f"每天早上7点起床。"),
        "回": (f" 毎日[まいにち] 6 時[じ]に{r}。", f"每天6点回去。"),
        "走": (f" 駅[えき]まで{r}。", f"走到车站。"),
        "跑": (f" 公園[こうえん]で{r}。", f"在公园跑步。"),
        "游": (f"プールで{r}。", f"在泳池游泳。"),
        "等": (f"ここで{r}。", f"在这里等。"),
        "说": (f" 日本語[にほんご]で{r}。", f"用日语说。"),
        "玩": (f" 公園[こうえん]で{r}。", f"在公园玩。"),
        "洗": (f" 手[て]を{r}。", f"洗手。"),
        "穿": (f"シャツを{r}。", f"穿衬衫。"),
        "脱": (f" 靴[くつ]を{r}。", f"脱鞋。"),
        "开": (f" 窓[まど]を{r}。", f"开窗。"),
        "关": (f"ドアを{r}。", f"关门。"),
        "拿": (f" 荷物[にもつ]を{r}。", f"拿行李。"),
        "送": (f" 荷物[にもつ]を{r}。", f"寄包裹。"),
        "借": (f" 本[ほん]を{r}。", f"借书。"),
        "住": (f" 東京[とうきょう]に{r}。", f"住在东京。"),
        "坐": (f" 椅子[いす]に{r}。", f"坐在椅子上。"),
        "站": (f"ここに{r}。", f"站在这里。"),
        "走路": (f" 駅[えき]まで{r}。", f"走到车站。"),
        "打电话": (f" 友達[ともだち]に{r}。", f"给朋友打电话。"),
        "结婚": (f" 来年[らいねん]{r}。", f"明年结婚。"),
        "散步": (f" 公園[こうえん]を{r}。", f"在公园散步。"),
        "使用": (f"パソコンを{r}。", f"使用电脑。"),
        "开始": (f" 授業[じゅぎょう]が{r}。", f"课开始了。"),
        "结束": (f" 授業[じゅぎょう]が{r}。", f"课结束了。"),
        "出": (f" 部屋[へや]を{r}。", f"出房间。"),
        "进": (f" 部屋[へや]に{r}。", f"进房间。"),
        "帮": (f" 友達[ともだち]を{r}。", f"帮朋友。"),
        "忘": (f" 名前[なまえ]を{r}。", f"忘了名字。"),
        "选": (f" 好[す]きなのを{r}。", f"选喜欢的。"),
        "决定": (f" 日[ひ]にちを{r}。", f"决定日期。"),
        "累": (f" 今日[きょう]は{r}。", f"今天累了。"),
        "下雨": (f" 明日[あした]{r}。", f"明天下雨。"),
        "迟到": (f" 会議[かいぎ]に{r}。", f"会议迟到了。"),
    }

    for keyword, (jp, cn_s) in patterns.items():
        if keyword in cn_clean:
            return jp, cn_s

    # Default verb pattern
    return f"{r}。", f"{cn_clean}。"


def _i_adj(key, raw, cn):
    """い-adjective example."""
    r = _use_raw(raw)
    cn_clean = cn.split("、")[0].split("（")[0].strip()

    subjects = {
        "大": "この 部屋[へや]", "小": "この 箱[はこ]", "新": "この パソコン",
        "旧": "この 建物[たてもの]", "好": " 今日[きょう]の 天気[てんき]",
        "坏": " 天気[てんき]", "热": " 今日[きょう]", "冷": " 冬[ふゆ]",
        "贵": "この 時計[とけい]", "便宜": "この 店[みせ]", "高": "この ビル",
        "低": "この テーブル", "矮": "この テーブル",
        "有趣": "この 映画[えいが]", "好吃": "この 料理[りょうり]",
        "忙": " 今週[こんしゅう]", "快乐": " 旅行[りょこう]",
        "难": " 日本語[にほんご]", "容易": "この 問題[もんだい]",
        "近": " 駅[えき]", "远": " 空港[くうこう]",
        "快": " 新幹線[しんかんせん]", "慢": "この バス",
        "重": "この 荷物[にもつ]", "轻": "この 鞄[かばん]",
        "多": " 人[ひと]が", "少": " 人[ひと]が",
        "甜": "このケーキ", "辣": "この 料理[りょうり]",
        "暖": " 春[はる]", "凉": " 秋[あき]",
        "蓝": " 空[そら]が", "红": "この 花[はな]",
        "白": "この シャツ", "黑": "この 鞄[かばん]",
        "宽": "この 部屋[へや]", "窄": "この 道[みち]",
        "早": " 朝[あさ]が",
    }

    subj = "これ"
    for kw, s in subjects.items():
        if kw in cn_clean:
            subj = s
            break

    if "が" in subj:
        return f"{subj}{r}です。", f"{cn_clean}。"
    return f"{subj}は {r}です。", f"{cn_clean}。"


def _na_adj(key, raw, cn):
    """な-adjective example."""
    r = _use_raw(raw)
    cn_clean = cn.split("、")[0].split("（")[0].strip()

    subjects = {
        "漂亮": "この 花[はな]", "干净": "この 部屋[へや]",
        "安静": " 図書館[としょかん]", "热闹": " 大阪[おおさか]",
        "有名": " 富士山[ふじさん]", "亲切": " 先生[せんせい]",
        "健康": "みんな", "方便": " 駅[えき]の 近[ちか]く",
        "喜欢": " 日本料理[にほんりょうり]が", "不喜欢": " 野菜[やさい]が",
        "擅长": " 料理[りょうり]が", "不擅长": " 運動[うんどう]が",
        "简单": "この 問題[もんだい]", "大变": " 仕事[しごと]が",
        "不行": "ここは", "重要": "この 書類[しょるい]",
        "特别": "この 料理[りょうり]", "必要": "パスポートが",
        "复杂": "この 問題[もんだい]", "自由": " 週末[しゅうまつ]は",
        "热情": "みんな", "无理": "それは",
    }

    subj = "ここ"
    for kw, s in subjects.items():
        if kw in cn_clean:
            subj = s
            break

    if "が" in subj:
        return f"{subj}{r}です。", f"{cn_clean}。"
    return f"{subj}は {r}です。", f"{cn_clean}。"


def _adverb(key, raw, cn):
    """Adverb example."""
    r = _use_raw(raw)
    cn_clean = cn.split("、")[0].split("（")[0].strip()
    return f"{r} 勉強[べんきょう]します。", f"{cn_clean}学习。"


def _interj(key, raw, cn):
    """Interjection."""
    return _use_raw(raw), cn.split("、")[0]


def _conj(key, raw, cn):
    """Conjunction."""
    r = _use_raw(raw)
    return f" 雨[あめ]です。{r} 寒[さむ]いです。", f"下雨了。{cn.split('、')[0]}很冷。"


def _noun(key, raw, cn):
    """Noun - default."""
    r = _use_raw(raw)
    cn_clean = cn.split("、")[0].split("（")[0].strip()

    # Location nouns
    if any(k in cn_clean for k in ["店", "馆", "院", "场", "室", "站"]):
        return f"{r}に 行[い]きました。", f"去了{cn_clean}。"
    # Food/drink
    if any(k in cn_clean for k in ["饭", "菜", "肉", "鱼", "果", "茶", "酒", "奶", "汁", "水"]):
        return f"{r}が 好[す]きです。", f"喜欢{cn_clean}。"
    # People
    if any(k in cn_clean for k in ["人", "员", "生", "师", "友", "孩", "妻", "夫", "父", "母", "姐", "哥", "弟", "妹"]):
        return f"{r}は 元気[げんき]です。", f"{cn_clean}很好。"
    # Time
    if any(k in cn_clean for k in ["月", "周", "天", "年", "季", "春", "夏", "秋", "冬"]):
        return f"{r}は 忙[いそが]しいです。", f"{cn_clean}很忙。"
    # Country/place
    if any(k in cn_clean for k in ["国", "京", "阪", "岛", "州", "港"]):
        return f"{r}に 行[い]きたいです。", f"想去{cn_clean}。"
    # Counter/number
    if any(k in cn_clean for k in ["个", "张", "台", "本", "杯", "次", "岁"]):
        return f"{r} 買[か]いました。", f"买了{cn_clean}。"

    # Default
    return f"{r}は どこですか。", f"{cn_clean}在哪里？"


def main():
    data = load_words()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for lesson_key in sorted(data.keys()):
        num = int(lesson_key.replace("第", "").replace("課", ""))
        if num < 9:
            continue  # Already done

        words = data[lesson_key]
        lesson_data = {}
        for w in words:
            if w["has_ex"]:
                continue  # Skip words that already have examples
            jp, cn = make_sentence(w["key"], w["raw"], w["pos"], w["cn"])
            lesson_data[w["key"]] = {"jp": jp, "cn": cn}

        outpath = os.path.join(OUTPUT_DIR, f"lesson_{num:02d}.json")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(lesson_data, f, ensure_ascii=False, indent=2)
        print(f"  {outpath}: {len(lesson_data)} entries")

    print("\nDone!")


if __name__ == "__main__":
    main()
