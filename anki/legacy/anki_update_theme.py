#!/usr/bin/env python3
"""
更新 Anki 卡片 UI：Duolingo 经典绿，无音频播放
"""
import json
import urllib.request

ANKI_URL = "http://localhost:8765"
MODEL = "日语单词卡片"


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(ANKI_URL, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    r = json.loads(resp.read())
    if r.get("error") and isinstance(r["error"], str):
        raise Exception(r["error"])
    return r.get("result")


CSS = r"""
/* ===== Duolingo Classic Green ===== */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&family=Noto+Sans+JP:wght@400;700;900&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  background: #235390;
  min-height: 100vh;
}

.card {
  font-family: 'Nunito', 'Noto Sans JP', 'Hiragino Sans', system-ui, sans-serif;
  background: #235390;
  color: #4b4b4b;
  max-width: 480px;
  margin: 0 auto;
  padding: 28px 16px;
  text-align: center;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* === 主卡片 === */
.card-box {
  background: #fff;
  border-radius: 16px;
  padding: 40px 30px 32px;
  box-shadow: 0 4px 0 #1a4373;
  animation: popIn 0.25s ease-out;
}

@keyframes popIn {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* === 提示文字 === */
.prompt {
  font-size: 16px;
  font-weight: 800;
  color: #afafaf;
  margin-bottom: 24px;
  letter-spacing: 0.3px;
}

/* === 日语主词 === */
.word {
  font-size: 52px;
  font-weight: 900;
  color: #3c3c3c;
  margin: 8px 0;
  letter-spacing: 4px;
  line-height: 1.3;
}

/* === 假名读音 === */
.reading {
  font-size: 22px;
  font-weight: 800;
  color: #1cb0f6;
  margin: 4px 0 10px;
  letter-spacing: 1px;
}

/* === 词性胶囊 === */
.pos-tag {
  display: inline-block;
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  background: #58cc02;
  padding: 5px 18px;
  border-radius: 20px;
  box-shadow: 0 3px 0 #43c000;
  margin: 10px 0 6px;
  letter-spacing: 0.5px;
}

/* === 释义区 === */
.meaning-block {
  text-align: left;
  margin: 22px 0 0;
  padding: 18px 22px;
  background: #f7f7f7;
  border-radius: 14px;
  border: 2px solid #e5e5e5;
  box-shadow: 0 2px 0 #e5e5e5;
}

.meaning-title {
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: #ff9600;
  margin-bottom: 8px;
}

.meaning-text {
  font-size: 20px;
  color: #3c3c3c;
  font-weight: 800;
  line-height: 1.7;
}

/* === 例句区 === */
.example-block {
  text-align: left;
  margin: 14px 0 0;
  padding: 16px 22px;
  background: #f7f7f7;
  border-radius: 14px;
  border: 2px solid #e5e5e5;
  border-left: 4px solid #58cc02;
}

.example-title {
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: #58cc02;
  margin-bottom: 6px;
}

.example-jp {
  font-size: 17px;
  color: #3c3c3c;
  font-weight: 700;
  line-height: 1.8;
}

/* === 课程标签 === */
.lesson-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 800;
  color: #afafaf;
  background: #f7f7f7;
  border: 2px solid #e5e5e5;
  padding: 4px 14px;
  border-radius: 20px;
  margin-top: 18px;
}

/* === 中文释义正面大字 === */
.meaning-front {
  font-size: 38px;
  font-weight: 900;
  color: #3c3c3c;
  margin: 8px 0;
  line-height: 1.4;
}

/* === 分隔线 === */
.divider {
  height: 2px;
  background: #e5e5e5;
  margin: 22px 0;
  border: none;
  border-radius: 1px;
}

/* === 打字输入 === */
#typeans {
  font-family: 'Nunito', 'Noto Sans JP', sans-serif !important;
  font-size: 28px !important;
  font-weight: 700 !important;
  text-align: center;
  padding: 14px 20px;
  border: 2.5px solid #e5e5e5;
  border-radius: 15px;
  background: #fff;
  color: #3c3c3c;
  width: 85%;
  max-width: 340px;
  margin: 16px auto;
  outline: none;
  box-shadow: 0 3px 0 #e5e5e5;
  transition: border-color 0.2s, box-shadow 0.2s;
}

#typeans:focus {
  border-color: #1cb0f6;
  box-shadow: 0 3px 0 #1cb0f6;
}

code#typeans {
  font-family: 'Nunito', 'Noto Sans JP', sans-serif !important;
  font-size: 28px !important;
  font-weight: 800 !important;
  padding: 12px 24px;
  border-radius: 15px;
  display: inline-block;
  background: transparent;
}

.typeGood {
  color: #58cc02 !important;
  font-weight: 900 !important;
  background: #d7ffb8 !important;
  padding: 3px 8px;
  border-radius: 8px;
}

.typeBad {
  color: #ff4b4b !important;
  font-weight: 900 !important;
  background: #ffdfe0 !important;
  text-decoration: line-through;
  padding: 3px 8px;
  border-radius: 8px;
}

.typeMissed {
  color: #afafaf !important;
  font-weight: 700 !important;
}

/* === 夜间模式 → 强制浅色 === */
.nightMode, .nightMode .card, .nightMode html, .nightMode body { background: #235390 !important; }
.nightMode .card-box { background: #fff !important; }
.nightMode .word { color: #3c3c3c !important; }
.nightMode .reading { color: #1cb0f6 !important; }
.nightMode .meaning-block, .nightMode .example-block { background: #f7f7f7 !important; border-color: #e5e5e5 !important; }
.nightMode .meaning-text, .nightMode .example-jp { color: #3c3c3c !important; }
.nightMode .prompt { color: #afafaf !important; }
.nightMode .meaning-front { color: #3c3c3c !important; }
.nightMode .pos-tag { background: #58cc02 !important; color: #fff !important; }
"""

# 日→中
FRONT_JP = """
<div class="card-box">
  <div class="prompt">这个词是什么意思？</div>
  <div class="word">{{日语}}</div>
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
</div>
"""

BACK_JP = """
<div class="card-box">
  <div class="word">{{日语}}</div>
  {{#读音}}<div class="reading">{{读音}}</div>{{/读音}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}

  <div class="meaning-block">
    <div class="meaning-title">释义</div>
    <div class="meaning-text">{{中文}}</div>
  </div>

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句</div>
    <div class="example-jp">{{例句}}</div>
  </div>
  {{/例句}}

  {{#课}}<div class="lesson-tag">{{课}}</div>{{/课}}
</div>
"""

# 中→日
FRONT_CN = """
<div class="card-box">
  <div class="prompt">日语怎么说？</div>
  <div class="meaning-front">{{中文}}</div>
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
</div>
"""

BACK_CN = """
<div class="card-box">
  <div class="word">{{日语}}</div>
  {{#读音}}<div class="reading">{{读音}}</div>{{/读音}}
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}

  <div class="meaning-block">
    <div class="meaning-title">释义</div>
    <div class="meaning-text">{{中文}}</div>
  </div>

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句</div>
    <div class="example-jp">{{例句}}</div>
  </div>
  {{/例句}}

  {{#课}}<div class="lesson-tag">{{课}}</div>{{/课}}
</div>
"""

# 拼写测试
FRONT_TYPE = """
<div class="card-box">
  <div class="prompt">请输入日语读音</div>
  <div class="meaning-front">{{中文}}</div>
  {{#词性}}<div class="pos-tag">{{词性}}</div>{{/词性}}
  <hr class="divider">
  {{type:读音}}
</div>
"""

BACK_TYPE = """
<div class="card-box">
  <div class="word">{{日语}}</div>
  {{#读音}}<div class="reading">{{读音}}</div>{{/读音}}
  <hr class="divider">
  {{type:读音}}

  <div class="meaning-block">
    <div class="meaning-title">释义</div>
    <div class="meaning-text">{{中文}}</div>
  </div>

  {{#例句}}
  <div class="example-block">
    <div class="example-title">例句</div>
    <div class="example-jp">{{例句}}</div>
  </div>
  {{/例句}}

  {{#课}}<div class="lesson-tag">{{课}}</div>{{/课}}
</div>
"""


def main():
    print("更新卡片 UI...")

    try:
        anki("version")
    except:
        print("✗ 请打开 Anki")
        return

    anki("updateModelStyling", model={"name": MODEL, "css": CSS})
    print("✓ CSS 已更新")

    anki("updateModelTemplates", model={
        "name": MODEL,
        "templates": {
            "日→中": {"Front": FRONT_JP, "Back": BACK_JP},
            "中→日": {"Front": FRONT_CN, "Back": BACK_CN},
            "拼写测试": {"Front": FRONT_TYPE, "Back": BACK_TYPE},
        },
    })
    print("✓ 3 个模板已更新（无音频播放）")
    print("✅ 完成！")


if __name__ == "__main__":
    main()
