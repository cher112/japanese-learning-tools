#!/usr/bin/env python3
"""
为 Anki 日语卡片生成 TTS 语音。
使用 OpenAI 兼容 API，音频文件通过 AnkiConnect 存入媒体库，iOS 同步可用。
"""

import json
import urllib.request
import base64
import time
import sys

# ============ 配置 ============
TTS_API_URL = "https://www.dmxapi.cn/v1/audio/speech"
TTS_API_KEY = "sk-xSnH2iKopoiPDZp78UBSDTHi4iugbv3VbXT3NlanJ8A3RF8t"
TTS_MODEL = "speech-2.6-hd"
TTS_VOICE = "female-shaonv"

ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = "日语N5单词"
MODEL_NAME = "日语单词卡片"
AUDIO_FIELD = "音声"  # 新增的音频字段


def anki_request(action, **params):
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


def generate_tts(text, filename):
    """调用 TTS API 生成音频，返回 base64 编码的音频数据"""
    payload = json.dumps({
        "model": TTS_MODEL,
        "voice": TTS_VOICE,
        "input": text,
    })
    req = urllib.request.Request(
        TTS_API_URL,
        data=payload.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TTS_API_KEY}",
        },
    )
    resp = urllib.request.urlopen(req, timeout=30)
    audio_data = resp.read()
    return base64.b64encode(audio_data).decode("utf-8")


def ensure_audio_field():
    """确保模型有音声字段"""
    fields = anki_request("modelFieldNames", modelName=MODEL_NAME)
    if AUDIO_FIELD not in fields:
        anki_request("modelFieldAdd", modelName=MODEL_NAME, fieldName=AUDIO_FIELD, index=6)
        print(f"✓ 已添加「{AUDIO_FIELD}」字段到模型")
    else:
        print(f"✓ 「{AUDIO_FIELD}」字段已存在")


def update_card_templates():
    """更新卡片模板，在背面加入音频播放"""
    # 获取当前模板
    models = anki_request("modelTemplates", modelName=MODEL_NAME)

    # 音频播放 HTML 片段
    audio_html = '\n  {{#音声}}<div class="audio-row">{{音声}}</div>{{/音声}}'

    for tpl_name in models:
        back = models[tpl_name]["Back"]
        if "音声" not in back:
            # 在 .word 后面插入音频
            back = back.replace(
                "</div>\n  {{#读音}}",
                f"</div>{audio_html}\n  {{{{#读音}}}}"
            )
            # fallback: 如果上面没替换成功，直接在第一个 </div> 后加
            if "音声" not in back:
                back = back.replace("</div>", f"</div>{audio_html}", 1)
            models[tpl_name]["Back"] = back

    anki_request(
        "updateModelTemplates",
        model={"name": MODEL_NAME, "templates": models},
    )
    print("✓ 卡片模板已更新（背面加入音频播放）")


def main():
    print("=" * 40)
    print("  Anki 日语 TTS 语音生成")
    print("=" * 40)

    # 1. 连接检查
    try:
        anki_request("version")
        print("✓ AnkiConnect 连接成功")
    except Exception:
        print("✗ 无法连接 AnkiConnect！请确保 Anki 已打开")
        return

    # 2. 确保音频字段存在
    ensure_audio_field()

    # 3. 获取所有卡片
    note_ids = anki_request("findNotes", query=f'"deck:{DECK_NAME}"')
    if not note_ids:
        print("✗ 牌组中没有卡片")
        return

    notes_info = anki_request("notesInfo", notes=note_ids)
    print(f"✓ 找到 {len(notes_info)} 张卡片")

    # 4. 逐个生成 TTS
    generated = 0
    skipped = 0
    failed = 0

    for i, note in enumerate(notes_info):
        fields = note["fields"]
        word = fields["日语"]["value"]
        reading = fields.get("读音", {}).get("value", "")
        audio_field = fields.get(AUDIO_FIELD, {}).get("value", "")

        # 跳过已有音频的
        if audio_field and "[sound:" in audio_field:
            skipped += 1
            continue

        # 用于 TTS 的文本：优先用读音（假名更准确）
        tts_text = reading if reading else word
        filename = f"jp_tts_{word}.mp3"

        sys.stdout.write(f"\r  [{i+1}/{len(notes_info)}] {word}（{tts_text}）...")
        sys.stdout.flush()

        try:
            # 生成音频
            audio_b64 = generate_tts(tts_text, filename)

            # 存入 Anki 媒体库
            anki_request(
                "storeMediaFile",
                filename=filename,
                data=audio_b64,
            )

            # 更新卡片的音声字段
            anki_request(
                "updateNoteFields",
                note={
                    "id": note["noteId"],
                    "fields": {AUDIO_FIELD: f"[sound:{filename}]"},
                },
            )

            generated += 1
            time.sleep(0.3)  # 避免 API 限流

        except Exception as e:
            print(f"\n  ✗ {word} 失败: {e}")
            failed += 1
            continue

    print(f"\n\n✓ TTS 生成完成:")
    print(f"  新生成: {generated}")
    print(f"  已跳过: {skipped}（已有音频）")
    if failed:
        print(f"  失败: {failed}")

    # 5. 更新卡片模板加入音频播放
    if generated > 0:
        update_card_templates()

    print("\n✅ 完成！翻牌时会自动播放日语发音")
    print("   同步到 AnkiWeb 后 iOS 也能听")


if __name__ == "__main__":
    main()
