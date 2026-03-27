#!/usr/bin/env python3
"""
從 store_notes.json 的文字描述，自動解析每家店的視覺 profile。
解析結果寫回 store_notes.json 的 visual_profile 欄位。

用法：
    python enrich_store_profiles.py [--store-notes ./data/store_notes.json] [--dry-run]
"""
import argparse
import json
import os
from pathlib import Path

import anthropic

_SYSTEM = """\
你是台灣魯肉飯的食物視覺分析專家。
根據店家的文字描述，提取可以從照片中辨識的視覺特徵。
只根據描述中明確提到的內容判斷，不要推測。
"""

_PROMPT_TEMPLATE = """\
以下是幾家魯肉飯店的描述，請為每家店提取視覺 profile。

{store_notes}

請以 JSON 回傳，格式如下（只回傳 JSON，不要其他文字）：
{{
  "店家名稱": {{
    "pork_part": "belly" | "fatty" | "lean" | "skin_heavy",
    "fat_ratio": "fat_heavy" | "balanced" | "lean_heavy",
    "skin": "with_skin" | "no_skin",
    "sauce_color": "light" | "medium" | "dark" | "black_gold",
    "rice_quality": "fluffy" | "soft" | "mushy"
  }},
  ...
}}

各欄位說明：

pork_part（肉的部位）：
- belly：帶皮五花肉，肥瘦相間層次分明
- fatty：肥肉為主，幾乎沒有瘦肉
- lean：瘦肉為主的細碎肉燥
- skin_heavy：大量豬皮，膠質豐富

fat_ratio（肥瘦比例）：
- fat_heavy：肥肉比例高，約七分肥三分瘦
- balanced：肥瘦均衡，約五五比
- lean_heavy：瘦肉比例高，約三分肥七分瘦

skin（豬皮）：
- with_skin：描述中有提到豬皮
- no_skin：沒有提到豬皮

sauce_color（醬汁顏色）：
- light：淡褐色、像湯汁、清淡
- medium：中等褐色、一般滷汁
- dark：深褐色、濃郁黏稠
- black_gold：黑糖色、焦糖化深黑

rice_quality（飯的口感）：
- fluffy：米粒鬆散分開
- soft：軟嫩帶點黏性
- mushy：偏爛、黏稠
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-notes", default="./data/store_notes.json")
    parser.add_argument("--dry-run", action="store_true", help="只顯示結果，不寫回檔案")
    args = parser.parse_args()

    notes_path = Path(args.store_notes)
    with open(notes_path, encoding="utf-8") as f:
        store_notes = json.load(f)

    store_text = ""
    for store_name, data in store_notes.items():
        notes = data.get("notes", "")
        store_text += f"【{store_name}】\n{notes}\n\n"

    prompt = _PROMPT_TEMPLATE.format(store_notes=store_text.strip())

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    print("送出解析請求（1 次 API call）...")

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        profiles = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失敗：{e}")
        print("原始回應：")
        print(raw)
        return

    # 顯示結果
    print("\n解析結果：\n" + "=" * 60)
    headers = ["pork_part", "fat_ratio", "skin", "sauce_color", "rice_quality"]
    labels = ["肉的部位", "肥瘦比例", "豬皮", "醬汁顏色", "飯的口感"]
    for store_name, profile in profiles.items():
        print(f"\n{store_name}")
        for key, label in zip(headers, labels):
            print(f"  {label}：{profile.get(key, '—')}")

    if args.dry_run:
        print("\n（dry-run 模式，未寫入檔案）")
        return

    # 寫回 store_notes.json
    matched = 0
    for store_name, profile in profiles.items():
        if store_name in store_notes:
            store_notes[store_name]["visual_profile"] = profile
            matched += 1
        else:
            print(f"  ⚠ 找不到店家：{store_name}")

    with open(notes_path, "w", encoding="utf-8") as f:
        json.dump(store_notes, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 寫入完成：{matched} 家店 → {notes_path}")


if __name__ == "__main__":
    main()
