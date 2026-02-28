#!/usr/bin/env python3
"""快速更新 CSS + 模板到两个 Profile（不重新导入卡片）"""
import json
import urllib.request
import os
import sys
import time

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
PROFILES = ["szmz", "czh"]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_apkg import CSS, FRONT_JP, BACK_JP, FRONT_CN, BACK_CN, MODEL


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

        # Ensure new fields exist
        fields = anki("modelFieldNames", modelName=MODEL)
        for fname in ["例句音频", "例句翻译"]:
            if fname not in fields:
                anki("modelFieldAdd", modelName=MODEL, fieldName=fname, index=len(fields))
                fields.append(fname)
                print(f"  + {profile}: {fname} 字段已添加")

        anki("updateModelStyling", model={"name": MODEL, "css": CSS})
        anki("updateModelTemplates", model={
            "name": MODEL,
            "templates": {
                "日文": {"Front": FRONT_JP, "Back": BACK_JP},
                "中文": {"Front": FRONT_CN, "Back": BACK_CN},
            }
        })
        print(f"  ✓ {profile}")

    try:
        anki("loadProfile", name="szmz")
    except Exception:
        pass
    time.sleep(3)
    print("✅ CSS 更新完成")


if __name__ == "__main__":
    main()
