#!/usr/bin/env python3
"""
同步词库到 czh 和 szmz 两个 Profile
切换 Profile → 导入/更新卡片 → 切换下一个
"""
import json
import urllib.request
import os
import sys
import time
import subprocess

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ANKI_URL = "http://localhost:8765"
PROFILES = ["szmz", "czh"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = _opener.open(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


def wait_for_anki(timeout=30):
    """Wait for AnkiConnect to be ready after profile switch"""
    for i in range(timeout):
        try:
            anki("version")
            return True
        except Exception:
            if i % 5 == 0:
                sys.stdout.write(f"\r  等待 Anki 就绪... ({i}s)")
                sys.stdout.flush()
            time.sleep(1)
    print()
    return False


def switch_profile(name):
    """Switch profile with robust retry logic"""
    # First try loadProfile
    try:
        result = anki("loadProfile", name=name)
        if result:
            time.sleep(5)
            if wait_for_anki(30):
                return True
    except Exception:
        pass

    # If loadProfile failed (connection reset during switch), wait longer
    print(f"  等待 Profile 切换完成...")
    time.sleep(8)
    return wait_for_anki(30)


def main():
    print("=" * 50)
    print("  同步词库 → czh + szmz")
    print("=" * 50)

    # Check Anki is running
    if not wait_for_anki(5):
        print("✗ 请打开 Anki")
        return

    profiles = anki("getProfiles")
    for p in PROFILES:
        if p not in profiles:
            print(f"✗ Profile「{p}」不存在")
            return

    for profile in PROFILES:
        print(f"\n{'─' * 50}")
        print(f"  切换到 Profile: {profile}")
        print(f"{'─' * 50}")

        if not switch_profile(profile):
            print(f"  ✗ 切换超时，跳过")
            continue

        print(f"  ✓ 已切换到 {profile}")

        # Run import script as subprocess
        import_script = os.path.join(SCRIPT_DIR, "import_apkg.py")
        proc = subprocess.run(
            [sys.executable, import_script],
            cwd=SCRIPT_DIR,
            capture_output=False,
        )
        if proc.returncode != 0:
            print(f"  ✗ 导入失败 (exit {proc.returncode})")

    # Switch back to szmz (your profile)
    print(f"\n{'─' * 50}")
    print("  切回 szmz")
    switch_profile("szmz")

    print(f"\n{'=' * 50}")
    print("  ✅ 两个 Profile 同步完成！")
    print("  czh 和 szmz 各自独立复习进度")
    print("  手机登录各自的 AnkiWeb 即可")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
