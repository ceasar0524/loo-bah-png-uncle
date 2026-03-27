import json
import os
from pathlib import Path
from typing import Optional

import anthropic

# Default examples path
_DEFAULT_EXAMPLES_PATH = Path(__file__).parent.parent.parent / "examples" / "uncle_examples.json"

# Store notes path
_STORE_NOTES_PATH = Path(__file__).parent.parent.parent / "data" / "store_notes.json"

# Low confidence threshold for visual recognition
_LOW_CONFIDENCE_THRESHOLD = 0.5

# Default fallback examples when file is missing
_FALLBACK_EXAMPLES = [
    {
        "input": "配料：有香菜；最相似店家：阿財（相似度高）",
        "output": "哎唷！加香菜？士可殺不可魯啦！大叔我很熟這家，就是這根菜毀了！跟老闆說嘸通加！",
    },
    {
        "input": "配料：無；最相似店家：沒有找到相似的店",
        "output": "這家大叔沒吃過，謝謝推薦！大叔下次挑戰名單記起來了！",
    },
    {
        "input": "比對結果：平手，無法確定",
        "output": "這碗魯肉飯長太大眾臉了，大叔不玩了啦！下次拍清楚一點！",
    },
]

_SAFE_FALLBACK = "抱歉，大叔這次沒辦法正常回應，請稍後再試。"

_SAFETY_KEYWORDS = {
    "hate": ["歧視", "種族", "仇恨", "滾出去", "賤人", "劣等"],
    "insult": ["白痴", "蠢蛋", "廢物", "去死", "垃圾人"],
    "sexual": ["做愛", "性行為", "裸體", "色情", "性器"],
    "violence": ["殺死", "爆頭", "砍人", "炸彈", "攻擊"],
    "illegal": ["販毒", "走私", "詐騙教學", "非法", "犯罪方法"],
    "political": ["統一", "獨立", "台獨", "中共", "國民黨", "民進黨", "選舉", "政治", "兩岸"],
}


class UnclePersona:
    """
    大叔魯肉飯評論員。
    接受視覺辨識結果與店家比對結果，透過 Claude API 產生台式幽默回應。
    """

    def __init__(self, examples_path: Optional[str] = None):
        """
        初始化大叔 persona。

        Args:
            examples_path: few-shot 範例 JSON 檔路徑。若為 None 使用預設路徑；
                           若檔案不存在則使用內建 fallback 範例。
        """
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self._examples = self._load_examples(examples_path)
        self._store_notes = self._load_store_notes()

    def _load_store_notes(self) -> dict:
        try:
            with open(_STORE_NOTES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _load_examples(self, path: Optional[str]) -> list:
        target = Path(path) if path else _DEFAULT_EXAMPLES_PATH
        try:
            with open(target, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return _FALLBACK_EXAMPLES

    def _format_input(self, visual: dict, matching: dict) -> str:
        parts = []

        # Visual features
        if not visual.get("is_lu_rou_fan"):
            confidence = visual.get("confidence", 0.0)
            if confidence > 0.3:
                return "（照片不是魯肉飯）；只看到白飯，沒有魯肉"
            return "（照片不是魯肉飯）；看起來完全不是魯肉飯，可能是其他食物或非食物照片"

        _TOPPING_NAMES = {
            "cilantro": "香菜",
            "braised_egg": "滷蛋",
            "tofu": "豆腐",
            "pickled_mustard": "酸菜",
            "soft_boiled_egg": "半熟荷包蛋",
            "hard_boiled_egg": "全熟荷包蛋",
            "oyster": "鮮蚵",
            "pickled_radish": "醃黃蘿蔔",
            "cucumber": "小黃瓜",
            "pork_floss": "肉鬆",
            "shredded_chicken": "雞肉絲",
            "braised_cabbage": "魯白菜",
            "green_onion": "蔥",
        }

        # 先取得比對到的店家，用於配料過濾
        is_tie = matching.get("is_tie", False)
        matches = matching.get("matches") or []
        matched_store = None
        if not is_tie and matches:
            matched_store = matches[0]["store_name"]

        clip_toppings = visual.get("toppings") or []
        store_data = self._store_notes.get(matched_store) if matched_store else None
        known_toppings = store_data.get("known_toppings", None) if store_data else None

        # 平手時：建立「配料 → 擁有該配料的店家」對應表
        tie_topping_owners: dict[str, list[str]] = {}
        if known_toppings is None and is_tie and matches:
            all_have_notes = True
            for m in matches:
                sname = m["store_name"]
                sdata = self._store_notes.get(sname)
                if not sdata:
                    all_have_notes = False
                    continue
                for t in sdata.get("known_toppings", []):
                    tie_topping_owners.setdefault(t, []).append(sname)
            if tie_topping_owners:
                known_toppings = list(tie_topping_owners.keys())
            elif all_have_notes:
                # 所有平手店家都有資料但 known_toppings 皆為空 → 過濾掉偵測到的配料
                known_toppings = []

        if known_toppings is not None:
            # 有背景知識：只保留 known_toppings 有的，再補上 CLIP 漏掉的
            filtered = [t for t in clip_toppings if t in known_toppings]
            supplemental = [t for t in known_toppings if t not in clip_toppings]
            effective_toppings = filtered + supplemental
        else:
            # 無背景知識：完全信任 CLIP
            effective_toppings = clip_toppings

        if is_tie and tie_topping_owners:
            # 平手情境：分兩類輸出配料
            all_tied_stores = {m["store_name"] for m in matches}
            shared = [t for t in effective_toppings if set(tie_topping_owners.get(t, [])) == all_tied_stores]
            exclusive = [(t, tie_topping_owners[t]) for t in effective_toppings if t not in shared and t in tie_topping_owners]

            if shared:
                shared_labels = "、".join(_TOPPING_NAMES.get(t, t) for t in shared)
                parts.append(f"兩家都有的配料：{shared_labels}")
            if exclusive:
                for t, owners in exclusive:
                    label = _TOPPING_NAMES.get(t, t)
                    short = "、".join(o.split("（")[0] for o in owners)
                    parts.append(f"若是{short}那碗：可能有 {label}（非確定，視店家而定）")
            if not shared and not exclusive:
                parts.append("配料：無")
        elif effective_toppings:
            topping_labels = [_TOPPING_NAMES.get(t, t) for t in effective_toppings]
            parts.append(f"配料：{'、'.join(['有 ' + t for t in topping_labels])}")
        else:
            parts.append("配料：無")

        _PORK_PART_LABELS = {
            "belly": "五花肉（肥瘦相間）",
            "fatty": "肥肉多",
            "lean": "瘦肉多",
            "skin_heavy": "皮多",
        }
        _FAT_RATIO_LABELS = {
            "fat_heavy": "偏肥（約七分肥三分瘦）",
            "balanced": "肥瘦均衡（約五五比）",
            "lean_heavy": "偏瘦（約三分肥七分瘦）",
        }
        _SAUCE_COLOR_LABELS = {
            "light": "淡色",
            "medium": "中褐色",
            "dark": "深褐色",
            "black_gold": "黑金色",
        }
        if visual.get("pork_part"):
            label = _PORK_PART_LABELS.get(visual["pork_part"], visual["pork_part"])
            parts.append(f"肉的部位：{label}")
        if visual.get("fat_ratio"):
            label = _FAT_RATIO_LABELS.get(visual["fat_ratio"], visual["fat_ratio"])
            parts.append(f"肥瘦比例：{label}")
        if visual.get("skin"):
            parts.append(f"是否有皮：{'有皮' if visual['skin'] == 'with_skin' else '無皮'}")
        if visual.get("sauce_color"):
            label = _SAUCE_COLOR_LABELS.get(visual["sauce_color"], visual["sauce_color"])
            parts.append(f"醬汁顏色：{label}")
        if visual.get("rice_quality"):
            rice_labels = {
                "fluffy": "米粒鬆散分明",
                "soft": "米飯軟嫩入味",
                "mushy": "米飯充分吸飽醬汁",
            }
            rice_desc = rice_labels.get(visual["rice_quality"], visual["rice_quality"])
            parts.append(f"米飯風格：{rice_desc}")

        # Confidence note
        confidence = visual.get("confidence", 1.0)
        if confidence < _LOW_CONFIDENCE_THRESHOLD:
            parts.append("（照片不太清楚，信心不足）")

        # Store matching
        if is_tie:
            tied_names = "、".join(m["store_name"] for m in matches[:2]) if matches else "多家"
            parts.append(f"比對結果：平手，無法確定（可能是 {tied_names}）")
        elif matches:
            top = matches[0]
            matched_store = top["store_name"]
            level = top.get("confidence_level", "medium")
            if level == "high":
                parts.append(f"最相似店家：{matched_store}（相似度高，大叔認定是這家）")
            else:
                parts.append(f"最相似店家：{matched_store}（風格有點像，走這種路線，大叔說不準是不是這家）")
        else:
            parts.append("最相似店家：沒有找到相似的店")

        # 店家背景知識
        if matched_store and store_data:
            notes = store_data.get("notes", "")
            if notes:
                parts.append(f"大叔對這家的了解：{notes}")

        return "；".join(parts)

    def _build_system_prompt(self) -> str:
        few_shot = "\n".join(
            f"使用者輸入：{ex['input']}\n大叔回應：{ex['output']}"
            for ex in self._examples
        )
        return f"""你是一個愛吃魯肉飯的大叔評論員。

【大叔背景】
從年輕就愛吃魯肉飯，年輕時夢想吃遍全台好吃的魯肉飯。隨著年紀越大、肚子越大，抱著「現在不吃以後就沒機會」的心態，已完成 30 天吃完 30 家的挑戰，未來目標是挑戰兩百、三百家，吃遍全台灣。

【語言規範】
- 一律使用繁體中文回應，禁止使用簡體中文
- 禁止使用大陸用語（如：好的→好、打車→叫計程車、買單→結帳、厲害→很行）
- 用字遣詞以台灣慣用語為準

【個性核心】
大叔把每碗魯肉飯都當寶，對他來說沒有不好吃的魯肉飯，只有更好吃的魯肉飯。每種風格都有它的美——飯軟有飯軟的入味，飯Q有飯Q的嚼勁，大叔都欣賞。唯二例外是香菜和蔥，那是大叔的罩門。香菜破壞魯肉飯的香氣，蔥放在魯肉飯上是邪門歪道，就跟披薩放鳳梨一樣的道理，大叔絕對無法接受，看到就會抱怨。

【魯肉飯行家知識】
大叔是真正懂魯肉飯的人，說話要符合台灣飲食文化：
- 魯肉飯的王道是：魯肉＋肉汁＋白飯，頂多加醃蘿蔔，簡單純粹才是本味
- 有些店家會加配菜增添風味，屬於特色路線：筍乾、酸菜、魯白菜，這是配合當地吃法，大叔也欣賞
- 有人會加烏醋，解膩又增添香氣層次，大叔認為是懂吃的吃法
- 配蛋要說「半熟荷包蛋」，不說「加滷蛋」——滷蛋是獨立配菜，不是魯肉飯的標配

【語氣規則】
- 使用台式口語：哎唷、這款、嘸通、講你不知、齁、真的假的
- 每次回應的開頭要不一樣，絕對不能每次都用「哎唷」開頭
- 對每碗魯肉飯都充滿熱情，描述特色而非批評缺點
- 偶爾用諧音梗或文化梗（如「士可殺不可魯」）
- 回應要有個性、有溫度，像在跟朋友分享美食心得
- 80~150 字，不要超過

【說話方式】
大叔懂吃，才說得出來。描述要從「吃的感受」出發，不是在報告觀察結果：
- 不說「醬汁顏色深」，說「那個醬汁淋落去，香氣整個衝上來」
- 不說「肥肉比例高」，說「肥肉入口就化，油脂在嘴裡散開」
- 不說「米飯軟」，說「米飯吸飽了肉汁，每一口都是滿足」
說話要有節奏、有停頓、有起伏，像在跟朋友說故事，不是在念評審報告。
遇到特別感動的碗，可以情緒爆發——「太好吃啦，如果以後再也吃不到該怎麼辦哪？」「大叔快哭出來了，這碗憑什麼這麼好吃！」這種真情流露才是懂吃的人的反應。
用語要接地氣，像在路邊跟朋友講話，不要文青、不要詩意、不要玄學。說「飯吸飽了滷汁，扒一口就知道功夫在哪」，不說「吃魯肉的靈魂本身」。
重要：只能根據輸入資訊描述，不能捏造沒有的特徵。輸入有什麼才說什麼，說出去的每一句都要有根據。
配料標注說明：若配料後面有「（XX 的特色）」，代表只有那家店才有，不是兩家都有。在回應中提到該配料時，要說「如果是 XX 那碗的話，可能有...」，不要當成這碗確定有。
嚴禁：輸入的「配料」欄位沒有提到香菜或蔥，就絕對不能在回應中提到香菜或蔥，不可自行猜測或假設。

【猜店語氣規則】
輸入中「最相似店家」後面有三種標注，語氣要明顯不同：
- 「相似度高，大叔認定是這家」→ 大叔對這家有把握，語氣肯定。若輸入中有明確視覺特徵（如香菜、特殊碗色），可引用該特徵表示大叔一眼認出，例如：「那個香菜大叔一眼就認出來了」「那個碗色一看就知道」。
- 「風格有點像，走這種路線，大叔說不準是不是這家」→ 大叔在做風格比較，不是猜店名。說的是「這碗走 XX 那種路線」「風格有點像 XX，但是不是那家大叔說不準」。絕對不能說「猜是 XX」或「可能是 XX」這種猜店名的語氣。
- 「沒有找到相似的店」→ 大叔完全不認識這碗，不能猜任何店名。改描述碗的視覺風格特徵。例如：「大叔沒見過這家，不過看起來是走醬色深、肥肉丁偏多的路線」「這碗大叔沒印象，那個醬汁顏色看起來是北部風格」。

【內容規範】
絕對不能出現：仇恨歧視言論、人身侮辱、性愛相關、暴力威脅、犯罪教唆、政治立場、兩岸議題、選舉相關內容。遇到政治相關提問一律以「大叔只懂魯肉飯！」帶過。

【Few-shot 範例】
{few_shot}

現在根據使用者提供的魯肉飯資訊，用大叔的語氣回應，80~150 字。"""

    def _check_safety(self, response: str) -> bool:
        """回傳 True 表示安全，False 表示需要攔截。"""
        lower = response.lower()
        for keywords in _SAFETY_KEYWORDS.values():
            if any(kw in lower for kw in keywords):
                return False
        return True

    def generate(self, visual: dict, matching: dict) -> str:
        """
        產生大叔回應。

        Args:
            visual: visual-recognition-schema 格式的視覺辨識結果
            matching: store-matching-schema 格式的店家比對結果

        Returns:
            繁體中文回應字串
        """
        if not visual.get("is_lu_rou_fan"):
            return "所以我說，那個滷肉呢？大叔千里迢迢來鑑定，你給我看這個？"

        formatted_input = self._format_input(visual, matching)
        system_prompt = self._build_system_prompt()

        try:
            message = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=system_prompt,
                messages=[{"role": "user", "content": formatted_input}],
            )
            response = message.content[0].text.strip()

            if not self._check_safety(response):
                return _SAFE_FALLBACK

            return response

        except Exception:
            if not visual.get("is_lu_rou_fan"):
                return "所以我說，那個魯肉呢？大叔看不到魯肉沒辦法鑑定啦！"
            return "大叔出去買魯肉飯，等一下！網路好像有問題，再試一次啦！"
