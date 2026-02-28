#!/usr/bin/env python3
"""设置 Anki 牌组选项 — 应用到两个 Profile
  単語: 百词斩风格（短间隔、高频复习）
  文法: 大间隔低频（~1周复习一轮）
"""
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

# ─── 牌组配置 ──────────────────────────────────────────
VOCAB_DECKS = ["みんなの日本語初级1-2 単語", "補充単語"]
GRAMMAR_DECK = "みんなの日本語初级1-2 文法"

# 百词斩风格（単語）
VOCAB_CONFIG = {
    "new_per_day": 50,
    "learning_steps": [1, 10],       # 1m → 10m（当天过两遍）
    "graduating_ivl": 1,             # Good 毕业: 1天
    "easy_ivl": 30,                  # Easy: 30天
    "rev_per_day": 100,
    "ease4": 2.5,                    # Easy加成 250%
    "max_ivl": 180,                  # 最大间隔 180天
}

# 大间隔低频（文法）— 1 周起步，按天递增
GRAMMAR_CONFIG = {
    "new_per_day": 20,               # 每天新语法点（139个，约1周学完）
    "learning_steps": [1440, 2880, 4320],  # 1天 → 2天 → 3天（纯按天递增）
    "graduating_ivl": 7,             # Good 毕业: 直接 7 天
    "easy_ivl": 21,                  # Easy: 3 周（已掌握→更久不见）
    "rev_per_day": 50,               # 文法量少，50 够用
    "ease4": 3.0,                    # Easy加成 300%（间隔增长更快）
    "max_ivl": 365,                  # 最大间隔 1 年
    "starting_ease": 3.0,            # 初始 ease 300%（默认250%太保守）
    "ivl_fct": 1.2,                  # 间隔修正系数 120%（全局拉大间隔）
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


def apply_config(deck_name, cfg, config_name=None):
    """Apply config dict to a deck. If config_name is given, ensure a
    dedicated config group exists and assign it to the deck + all sub-decks."""
    try:
        config = anki("getDeckConfig", deck=deck_name)
    except Exception as e:
        print(f"    ✗ {deck_name}: {e}")
        return False

    # If we need a dedicated config group, create one via cloneDeckConfigId
    if config_name and config["name"] != config_name:
        try:
            new_id = anki("cloneDeckConfigId",
                          name=config_name, cloneFrom=config["id"])
            # Assign to this deck
            anki("setDeckConfigId", decks=[deck_name], configId=new_id)
            # Re-fetch the new config
            config = anki("getDeckConfig", deck=deck_name)
            print(f"    + 选项组「{config_name}」(id={new_id})")
        except Exception as e:
            # Maybe already exists — find it
            all_configs = anki("getDeckConfigNames")  # not available
            print(f"    ⚠ clone failed: {e}, using existing config")

    # New cards
    config["new"]["perDay"] = cfg["new_per_day"]
    config["new"]["learningSteps"] = cfg["learning_steps"]
    config["new"]["graduatingIvl"] = cfg["graduating_ivl"]
    config["new"]["easyIvl"] = cfg["easy_ivl"]

    # Reviews
    config["rev"]["perDay"] = cfg["rev_per_day"]
    config["rev"]["ease4"] = cfg["ease4"]
    config["rev"]["maxIvl"] = cfg["max_ivl"]
    if "ivl_fct" in cfg:
        config["rev"]["ivlFct"] = cfg["ivl_fct"]

    try:
        anki("saveDeckConfig", config=config)
    except Exception as e:
        print(f"    ✗ {deck_name}: {e}")
        return False

    # Assign this config to ALL sub-decks too
    config_id = config["id"]
    all_decks = anki("deckNames")
    sub_decks = [d for d in all_decks if d.startswith(deck_name + "::")]
    if sub_decks:
        anki("setDeckConfigId", decks=sub_decks, configId=config_id)

    print(f"    ✓ {deck_name} + {len(sub_decks)} sub-decks → 「{config['name']}」")
    return True


def main():
    if not wait(5):
        print("✗ 请打开 Anki")
        return

    for profile in PROFILES:
        print(f"\n  [{profile}]")
        try:
            anki("loadProfile", name=profile)
        except Exception:
            pass
        time.sleep(10)
        if not wait():
            print(f"    ✗ 超时")
            continue

        # 単語（用"系统默认"即可，先配置）
        for deck in VOCAB_DECKS:
            apply_config(deck, VOCAB_CONFIG)

        # 文法（独立选项组「文法」，含所有子牌组）
        apply_config(GRAMMAR_DECK, GRAMMAR_CONFIG, config_name="文法")

    # Switch back
    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)

    print("\n" + "=" * 55)
    print("  ✅ 牌组选项已更新")
    print("=" * 55)

    print("\n  【単語】百词斩风格")
    print(f"    新卡片: {VOCAB_CONFIG['new_per_day']}/天")
    print(f"    学习步骤: {' → '.join(str(s)+'m' if s<60 else str(s//60)+'h' if s<1440 else str(s//1440)+'d' for s in VOCAB_CONFIG['learning_steps'])}")
    print(f"    Good 毕业: {VOCAB_CONFIG['graduating_ivl']}天")
    print(f"    Easy: {VOCAB_CONFIG['easy_ivl']}天")
    print(f"    复习上限: {VOCAB_CONFIG['rev_per_day']}/天")
    print(f"    最大间隔: {VOCAB_CONFIG['max_ivl']}天")

    def fmt_steps(steps):
        parts = []
        for s in steps:
            if s < 60:
                parts.append(f"{s}m")
            elif s < 1440:
                parts.append(f"{s//60}h")
            else:
                parts.append(f"{s//1440}d")
        return " → ".join(parts)

    print(f"\n  【文法】大间隔低频（~1周复习）")
    print(f"    新卡片: {GRAMMAR_CONFIG['new_per_day']}/天")
    print(f"    学习步骤: {fmt_steps(GRAMMAR_CONFIG['learning_steps'])}")
    print(f"    Good 毕业: {GRAMMAR_CONFIG['graduating_ivl']}天")
    print(f"    Easy: {GRAMMAR_CONFIG['easy_ivl']}天")
    print(f"    初始 Ease: {int(GRAMMAR_CONFIG['starting_ease']*100)}%")
    print(f"    Easy加成: {int(GRAMMAR_CONFIG['ease4']*100)}%")
    print(f"    间隔修正: {int(GRAMMAR_CONFIG['ivl_fct']*100)}%")
    print(f"    复习上限: {GRAMMAR_CONFIG['rev_per_day']}/天")
    print(f"    最大间隔: {GRAMMAR_CONFIG['max_ivl']}天")

    print(f"\n  文法复习节奏示例:")
    print(f"    新卡 → 1d → 2d → 3d → 毕业(7d)")
    print(f"    Good: 7d → 21d → 63d → 189d → 365d")
    print(f"    Easy: 21d → 63d → 189d → 365d")


if __name__ == "__main__":
    main()
