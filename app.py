import logging
import os
import tempfile
import threading
import time

logging.basicConfig(level=logging.INFO)

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
    TextMessage,
)
from linebot.v3.messaging import (
    LocationAction,
    MessageAction,
    QuickReply,
    QuickReplyItem,
)
from linebot.v3.messaging import (
    FlexMessage,
    FlexBubble,
    FlexBubbleStyles,
    FlexBlockStyle,
    FlexBox,
    FlexButton,
    FlexText,
    FlexSeparator,
    URIAction,
)
from linebot.v3.webhooks import ImageMessageContent, LocationMessageContent, MessageEvent, TextMessageContent

from src import clip_model
from src.nearby_search import search_nearby_stores, search_random_nearby_store
from src.pipeline import run as pipeline_run
from src.uncle_persona.persona import UnclePersona

import json
from pathlib import Path

_STORE_NOTES_PATH = Path(__file__).parent / "data" / "store_notes.json"
_store_notes: dict = {}
try:
    with open(_STORE_NOTES_PATH, encoding="utf-8") as f:
        _store_notes = json.load(f)
except Exception:
    pass

_HIDDEN_GEMS_PATH = Path(__file__).parent / "data" / "hidden_gems.json"
_hidden_gems: dict = {}
try:
    with open(_HIDDEN_GEMS_PATH, encoding="utf-8") as f:
        _hidden_gems = json.load(f)
except Exception:
    pass

# 是否將巷仔口店家納入隨機驚喜 pool（改 False 可快速關掉）
_HIDDEN_GEMS_IN_RANDOM = True
# 巷仔口中與 _store_notes 實為同一家但名稱不同的店，排除避免重複推薦
_HIDDEN_GEMS_RANDOM_EXCLUDE = {"筒仔米糕滷肉飯貢丸湯（泰山區）"}

def _build_random_pool() -> dict:
    if not _HIDDEN_GEMS_IN_RANDOM:
        return _store_notes
    pool = dict(_store_notes)
    for name, data in _hidden_gems.items():
        if name not in pool and name not in _HIDDEN_GEMS_RANDOM_EXCLUDE:
            pool[name] = data
    return pool

_random_pool = _build_random_pool()

# Firestore 統計
try:
    from google.cloud import firestore as _firestore
    _db = _firestore.Client()
    _stats_ref = _db.collection("stats").document("events")
except Exception:
    _db = None
    _stats_ref = None

def _track(event: str, extra_field: str | None = None) -> None:
    """非同步記錄事件到 Firestore（失敗不影響主流程）。"""
    if _db is None:
        return
    def _write():
        try:
            from datetime import datetime
            import zoneinfo
            today = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")
            updates = {event: _firestore.Increment(1)}
            if extra_field:
                updates[extra_field] = _firestore.Increment(1)
            # 總計
            _db.collection("stats").document("events").set(updates, merge=True)
            # 每日
            _db.collection("stats").document(today).set(updates, merge=True)
        except Exception:
            pass
    threading.Thread(target=_write, daemon=True).start()


def _is_currently_open(periods: list, current_day: int, current_hour: int, current_minute: int) -> bool:
    """判斷店家現在是否在營業時間內。current_day 為 Google Places 格式（Sunday=0）。"""
    for period in periods:
        open_info = period.get("open", {})
        close_info = period.get("close")
        open_day = open_info.get("day", -1)
        open_total = open_info.get("hour", 0) * 60 + open_info.get("minute", 0)
        if close_info is None:
            return True  # 24 小時營業
        close_day = close_info.get("day", -1)
        close_total = close_info.get("hour", 23) * 60 + close_info.get("minute", 59)
        current_total = current_hour * 60 + current_minute
        if open_day == close_day:
            if current_day == open_day and open_total <= current_total < close_total:
                return True
        else:
            # 跨天（例如 23:00 ~ 02:00）
            if current_day == open_day and current_total >= open_total:
                return True
            if current_day == close_day and current_total < close_total:
                return True
    return False


def _get_open_pool() -> dict:
    """回傳目前營業中的店家 pool，無時間資料的店一律保留。"""
    from datetime import datetime
    import zoneinfo
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei"))
    google_day = now.isoweekday() % 7  # Mon=1..Sun=7 → Mon=1..Sun=0
    current_hour = now.hour
    current_minute = now.minute
    filtered = {}
    for name, data in _random_pool.items():
        hours_entry = _store_hours.get(name)
        if not hours_entry or not hours_entry.get("hours"):
            filtered[name] = data
            continue
        periods = hours_entry["hours"].get("periods", [])
        if not periods:
            filtered[name] = data
            continue
        if _is_currently_open(periods, google_day, current_hour, current_minute):
            filtered[name] = data
    return filtered


_STORE_HOURS_PATH = Path(__file__).parent / "data" / "store_hours.json"
_store_hours: dict = {}
try:
    with open(_STORE_HOURS_PATH, encoding="utf-8") as f:
        _store_hours = json.load(f)
except Exception:
    pass

_persona = UnclePersona()

# 啟動時預載 CLIP 模型，避免第一個請求才觸發載入
clip_model.get_model()

app = Flask(__name__)

# 啟動時讀取，缺少則立即 KeyError 報錯
_LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
_LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

# 附近推薦功能開關（設為 "false" 可快速關閉，不影響辨識流程）
NEARBY_SEARCH_ENABLED = os.getenv("NEARBY_SEARCH_ENABLED", "true").lower() == "true"

# Admin user ID，過濾測試流量不計入統計
_ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")


def _is_admin(user_id: str) -> bool:
    return bool(_ADMIN_USER_ID) and user_id == _ADMIN_USER_ID

# Session：暫存用戶查詢的辨識結果，供附近推薦使用
# 格式：{user_id: {"store": str, "ts": float, "seen": set, "expanded": bool}}
_SESSION_TTL = 300  # 5 分鐘
_RANDOM_SESSION = "__random__"  # 隨機驚喜模式的 session 標記
_sessions: dict = {}
_sessions_lock = threading.Lock()


def _cleanup_sessions() -> None:
    """移除超過 TTL 的 session（在 lock 內呼叫）。"""
    now = time.time()
    expired = [uid for uid, v in _sessions.items() if now - v["ts"] > _SESSION_TTL]
    for uid in expired:
        del _sessions[uid]


def _save_session(user_id: str, matched_store: str) -> None:
    with _sessions_lock:
        _cleanup_sessions()
        existing = _sessions.get(user_id)
        if existing and existing.get("store") == matched_store:
            # 同模式連按：保留 seen，只更新 ts
            existing["ts"] = time.time()
        else:
            _sessions[user_id] = {"store": matched_store, "ts": time.time(), "seen": set()}


def _get_session(user_id: str):
    """回傳 matched_store，若無 session 或已過期則回傳 None。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        if time.time() - entry["ts"] > _SESSION_TTL:
            del _sessions[user_id]
            return None
        return entry["store"]


def _get_seen(user_id: str) -> set:
    """回傳隨機驚喜已推薦過的店家集合。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return set()
        return set(entry["seen"])


def _add_to_seen(user_id: str, store_name: str) -> None:
    """將店家加入已推薦紀錄。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry["seen"].add(store_name)


def _reset_seen(user_id: str) -> None:
    """清空已推薦紀錄（全抽完後重置）。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry["seen"] = set()
            entry["expanded"] = False


def _get_expanded(user_id: str) -> bool:
    """回傳是否已進入擴大範圍模式。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return False
        return entry.get("expanded", False)


def _set_expanded(user_id: str, value: bool) -> None:
    """設定擴大範圍模式旗標。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry["expanded"] = value


_TASTE_SESSION = "__taste__"  # 個人化推薦模式的 session 標記

# 個人化問卷題目定義
_TASTE_QUIZ_QUESTIONS = [
    {
        "question": "肉質偏好？",
        "options": ["偏肥", "偏瘦", "都可以"],
        "field": "fat_ratio",
        "source": "visual_profile",
        "mapping": {"偏肥": "fat_heavy", "偏瘦": "lean_heavy", "都可以": None},
    },
    {
        "question": "喜歡黏一點？",
        "options": ["黏黏", "不黏", "都可以"],
        "field": "skin",
        "source": "visual_profile",
        "mapping": {"黏黏": "with_skin", "不黏": "no_skin", "都可以": None},
    },
    {
        "question": "滷汁濃稠？",
        "options": ["稠", "不稠", "都可以"],
        "field": "sauce_consistency",
        "source": "top_level",
        "mapping": {"稠": "稠", "不稠": "水", "都可以": None},
    },
    {
        "question": "口味偏好？",
        "options": ["偏甜（南部）", "偏鹹（北部）", "都可以"],
        "field": "sauce_taste",
        "source": "visual_profile",
        "mapping": {"偏甜（南部）": "偏甜", "偏鹹（北部）": "偏鹹", "都可以": None},
    },
]
_TASTE_QUIZ_ALL_OPTIONS = {
    opt for q in _TASTE_QUIZ_QUESTIONS for opt in q["options"]
}


def _save_taste_quiz(user_id: str, step: int, answers: dict) -> None:
    """儲存個人化問卷進度到 session 的獨立 key，不影響現有 store/seen/expanded。"""
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["taste_quiz"] = {"step": step, "answers": answers}
        _sessions[user_id]["ts"] = time.time()


def _get_taste_quiz(user_id: str) -> dict | None:
    """回傳個人化問卷進度，若無則回傳 None。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        if time.time() - entry["ts"] > _SESSION_TTL:
            del _sessions[user_id]
            return None
        return entry.get("taste_quiz")


def _clear_taste_quiz(user_id: str) -> None:
    """清除個人化問卷 session state。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("taste_quiz", None)


def _save_last_location(user_id: str, lat: float, lng: float) -> None:
    """將用戶最後一次分享的位置存入 session，供後續「附近巷仔口店家」直接查附近店用。"""
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["last_location"] = {"lat": lat, "lng": lng}
        _sessions[user_id]["ts"] = time.time()


def _get_last_location(user_id: str) -> dict | None:
    """回傳上次存的位置，若無或已過期則回傳 None。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        if time.time() - entry.get("ts", 0) > _SESSION_TTL:
            return None
        return entry.get("last_location")


def _clear_last_location(user_id: str) -> None:
    """清除存的位置。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("last_location", None)


# ── Firestore 口味偏好持久化 ──────────────────────────────────────────────────

def _save_taste_preference(user_id: str, answers: dict) -> None:
    """非同步將口味偏好存入 Firestore user_preferences collection。"""
    if _db is None:
        return
    def _write():
        from datetime import datetime, timezone
        try:
            _db.collection("user_preferences").document(user_id).set({
                "taste": answers,
                "updated_at": datetime.now(timezone.utc),
            })
        except Exception:
            pass
    threading.Thread(target=_write, daemon=True).start()


def _load_taste_preference(user_id: str) -> dict | None:
    """從 Firestore 讀取用戶口味偏好，回傳 answers dict 或 None。"""
    if _db is None:
        return None
    try:
        doc = _db.collection("user_preferences").document(user_id).get()
        if doc.exists:
            return doc.to_dict().get("taste")
        return None
    except Exception:
        return None


def _taste_preference_summary(answers: dict) -> str:
    """將口味偏好 answers 轉為可讀摘要，例如「偏瘦・不黏・不稠・偏鹹」。"""
    labels = {
        "fat_ratio":         {"fat_heavy": "偏肥", "lean_heavy": "偏瘦", None: "肉質都可以"},
        "skin":              {"with_skin": "黏黏",  "no_skin":    "不黏", None: "黏度都可以"},
        "sauce_consistency": {"稠": "稠",            "水":          "不稠", None: "濃稠都可以"},
        "sauce_taste":       {"偏甜": "偏甜",        "偏鹹":        "偏鹹", None: "口味都可以"},
    }
    parts = []
    for field in ["fat_ratio", "skin", "sauce_consistency", "sauce_taste"]:
        val = answers.get(field)
        parts.append(labels[field].get(val, str(val) if val else "都可以"))
    return "・".join(parts)


# ── taste_save_pending session helpers ───────────────────────────────────────

def _save_taste_save_pending(user_id: str, answers: dict) -> None:
    """儲存待確認儲存的口味答案。"""
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["taste_save_pending"] = answers
        _sessions[user_id]["ts"] = time.time()


def _get_taste_save_pending(user_id: str) -> dict | None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        return entry.get("taste_save_pending")


def _clear_taste_save_pending(user_id: str) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("taste_save_pending", None)


# ── taste_loaded session helpers ─────────────────────────────────────────────

def _save_taste_loaded(user_id: str, answers: dict) -> None:
    """儲存從 Firestore 讀取的偏好，供「直接用」流程使用。"""
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["taste_loaded"] = answers
        _sessions[user_id]["ts"] = time.time()


def _get_taste_loaded(user_id: str) -> dict | None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        return entry.get("taste_loaded")


def _clear_taste_loaded(user_id: str) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("taste_loaded", None)


_handler = WebhookHandler(_LINE_CHANNEL_SECRET)
_config = Configuration(access_token=_LINE_CHANNEL_ACCESS_TOKEN)


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        _handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


def _process_image(reply_token, message_id, user_id):
    if not _is_admin(user_id):
        logging.info("[event] image_received")
        _track("image_received")

    with ApiClient(_config) as api_client:
        blob_api = MessagingApiBlob(api_client)
        image_bytes = blob_api.get_message_content(message_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        reply_text, matched_store = pipeline_run(tmp_path, index_path="index.npz")
    except Exception:
        import traceback
        traceback.print_exc()
        reply_text = "大叔出去買魯肉飯，等一下！再試一次啦！"
        matched_store = None
    finally:
        os.unlink(tmp_path)

    if not _is_admin(user_id) and matched_store:
        logging.info("[event] recognition_success store=%s", matched_store)

    if NEARBY_SEARCH_ENABLED and matched_store:
        _save_session(user_id, matched_store)

    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            if NEARBY_SEARCH_ENABLED and matched_store:
                msg = TextMessage(
                    text=reply_text,
                    quick_reply=QuickReply(items=[
                        QuickReplyItem(action=LocationAction(label="找附近類似的 📍"))
                    ]),
                )
            else:
                msg = TextMessage(text=reply_text)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[msg],
                )
            )
    except Exception:
        import traceback
        traceback.print_exc()


def _build_random_flex(result: dict) -> FlexMessage:
    """組裝隨機驚喜的 Flex Message。"""
    name = result["store_name"]
    dist = result["distance_km"]
    loc = _random_pool.get(name, {}).get("location", {})
    maps_url = f"https://maps.google.com/?q={loc['lat']},{loc['lng']}"
    far_phrase = _persona.get_random_far_phrase(dist)
    tagline = _store_notes.get(name, {}).get("random_tagline", "") if not far_phrase else ""
    phrase = far_phrase or tagline

    contents = [
        FlexText(text="大叔今天幫你決定！🎲", weight="bold", size="md"),
    ]

    if phrase:
        contents += [
            FlexSeparator(margin="lg"),
            FlexText(text=f"📜  {phrase}", weight="bold", size="xl",
                     color="#8B4513", align="center", margin="lg"),
            FlexSeparator(margin="lg"),
        ]
    else:
        contents.append(FlexSeparator(margin="md"))

    display_note = _store_notes.get(name, {}).get("display_note", "")
    contents += [
        FlexText(text=name, weight="bold", size="md", margin="md", wrap=True),
    ]
    if display_note:
        contents.append(FlexText(text=display_note, size="sm", color="#888888"))
    contents += [
        FlexText(text=f"距你約 {dist} 公里", size="sm", color="#888888"),
        FlexButton(
            action=URIAction(label="📍 地圖", uri=maps_url),
            style="primary",
            margin="md",
            height="sm",
        ),
        FlexSeparator(margin="md"),
        FlexText(text="⏰ 出發前請參考各家營業時間",
                 size="xs", color="#888888", wrap=True, margin="md"),
    ]

    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    return FlexMessage(alt_text="大叔今天幫你決定！", contents=bubble)


def _build_exhausted_flex() -> FlexMessage:
    """抽太多次後出現的彩蛋 Flex Message，隨機二選一。"""
    import random
    eggs = [
        {
            "tagline": "📜  一直抽、一直抽，啊是欲食無？\n你今仔日攏免食飯啦！",
            "store": "自己家",
        },
        {
            "tagline": "📜  一直抽、一直抽，我懷疑你今天是來遛皮克敏，不是來吃魯肉飯的",
            "store": "花圃",
        },
    ]
    egg = random.choice(eggs)
    contents = [
        FlexText(text="大叔今天網路用夠多了 🖥️", weight="bold", size="md"),
        FlexSeparator(margin="lg"),
        FlexText(text=egg["tagline"],
                 weight="bold", size="xl", color="#8B4513", align="center",
                 margin="lg", wrap=True),
        FlexSeparator(margin="lg"),
        FlexText(text=egg["store"], weight="bold", size="md", margin="md", wrap=True),
        FlexButton(
            action=URIAction(label="📍 地圖", uri="https://maps.google.com/"),
            style="primary",
            margin="md",
            height="sm",
            disabled=True,
        ),
    ]
    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    return FlexMessage(alt_text="大叔今天幫你決定！", contents=bubble)


def _build_nearby_flex(results: list) -> FlexMessage:
    """組裝風格相近推薦的 Flex Message（最多 2 家）。"""
    contents = [
        FlexText(text="大叔雷達掃到了！附近走類似風格的：", weight="bold", size="md", wrap=True),
    ]

    for r in results:
        name = r["store_name"]
        dist = r["distance_km"]
        maps_url = _persona.maps_url(name)
        display_note = _store_notes.get(name, {}).get("display_note", "")

        contents.append(FlexSeparator(margin="lg"))
        contents.append(FlexText(text=name, weight="bold", size="md", margin="md", wrap=True))
        if display_note:
            contents.append(FlexText(text=display_note, size="sm", color="#888888"))
        contents.append(FlexText(text=f"距你約 {dist} 公里", size="sm", color="#888888"))
        contents.append(FlexButton(
            action=URIAction(label="📍 地圖", uri=maps_url),
            style="primary",
            margin="md",
            height="sm",
        ))

    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    return FlexMessage(alt_text="大叔雷達掃到了！", contents=bubble)


def _score_store_taste(store_info: dict, answers: dict) -> int:
    """計算店家與用戶口味偏好的符合分數（0–4）。"""
    score = 0
    vp = store_info.get("visual_profile", {})
    for q in _TASTE_QUIZ_QUESTIONS:
        field = q["field"]
        source = q["source"]
        user_val = answers.get(field)  # None 表示「都可以」
        if user_val is None:
            score += 1
            continue
        if source == "top_level":
            store_val = store_info.get(field)
        else:
            store_val = vp.get(field)
        if store_val == user_val:
            score += 1
    return score


def _match_taste_stores(lat: float, lng: float, answers: dict, radius_km: float = 10.0) -> list:
    """依口味偏好比對 store_notes 店家，回傳分數最高、距離最近的 2–3 家。"""
    from src.nearby_search.searcher import haversine_km
    candidates = []
    for name, info in _store_notes.items():
        loc = info.get("location")
        if not loc:
            continue
        dist = haversine_km(lat, lng, loc["lat"], loc["lng"])
        if dist > radius_km:
            continue
        score = _score_store_taste(info, answers)
        candidates.append({"store_name": name, "distance_km": round(dist, 1), "score": score, "info": info})

    # 依分數降冪、距離升冪排序
    candidates.sort(key=lambda x: (-x["score"], x["distance_km"]))
    return candidates


def _generate_taste_intros(stores: list) -> dict:
    """呼叫 Claude Haiku 為每家推薦店生成大叔風格介紹（30 字以內）。回傳 {store_name: intro}。"""
    import anthropic as _anthropic
    import os as _os
    client = _anthropic.Anthropic(api_key=_os.environ.get("ANTHROPIC_API_KEY"))

    store_inputs = []
    for s in stores:
        name = s["store_name"]
        info = s["info"]
        notes = info.get("notes", "")
        toppings = info.get("available_toppings", [])
        topping_str = f"，可加點：{'、'.join(toppings)}" if toppings else ""
        store_inputs.append(f"【{name}】{notes[:150]}{topping_str}")

    combined = "\n\n".join(store_inputs)
    prompt = (
        f"你是一個台灣大叔，熱愛魯肉飯，說話直接有個性。\n"
        f"以下是幾家店的資料，請為每家店各寫一句30字以內的介紹，用大叔口吻，格式如下：\n"
        f"【店名】：介紹文\n\n"
        f"{combined}"
    )
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        logging.info(f"[taste_intros] raw: {raw}")
        raw_intros = {}
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("【") and "】" in line:
                for sep in ["】：", "】:"]:
                    if sep in line:
                        parts = line.split(sep, 1)
                        key = parts[0][1:]
                        raw_intros[key] = parts[1].strip()
                        break
        # 精確比對，對不上再用相似度比對
        from difflib import get_close_matches
        store_names = [s["store_name"] for s in stores]
        intros = {}
        for raw_key, intro in raw_intros.items():
            if raw_key in store_names:
                intros[raw_key] = intro
            else:
                matched_list = get_close_matches(raw_key, store_names, n=1, cutoff=0.8)
                if matched_list:
                    intros[matched_list[0]] = intro
        return intros
    except Exception:
        return {}


def _build_taste_loaded_flex(answers: dict) -> FlexMessage:
    """顯示已儲存的口味偏好摘要，供用戶確認直接用或重新填。"""
    labels = {
        "fat_ratio":         {"fat_heavy": "偏肥", "lean_heavy": "偏瘦", None: "都可以"},
        "skin":              {"with_skin": "黏黏",  "no_skin":    "不黏", None: "都可以"},
        "sauce_consistency": {"稠": "稠",            "水":          "不稠", None: "都可以"},
        "sauce_taste":       {"偏甜": "偏甜",        "偏鹹":        "偏鹹", None: "都可以"},
    }
    rows = [
        ("🍖", labels["fat_ratio"].get(answers.get("fat_ratio"), "都可以")),
        ("💋", labels["skin"].get(answers.get("skin"), "都可以")),
        ("🍯", labels["sauce_consistency"].get(answers.get("sauce_consistency"), "都可以")),
        ("🧂", labels["sauce_taste"].get(answers.get("sauce_taste"), "都可以")),
    ]
    header = FlexBox(
        layout="vertical",
        background_color="#6A3F2D",
        padding_all="lg",
        contents=[
            FlexText(text="🍚 大叔記得你的口味", weight="bold", size="md", color="#FFFFFF"),
        ],
    )
    body_contents = []
    for emoji, value in rows:
        body_contents.append(FlexBox(
            layout="horizontal",
            justify_content="center",
            align_items="center",
            margin="lg",
            contents=[
                FlexText(text=emoji, size="xl", flex=0),
                FlexText(text=f"  {value}", size="xl", weight="bold", color="#4B2F24", flex=0),
            ],
        ))
    bubble = FlexBubble(
        header=header,
        body=FlexBox(layout="vertical", contents=body_contents, padding_all="lg"),
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#E9E1D8"),
        ),
    )
    qr = QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="直接用 ✅", text="直接用 ✅")),
        QuickReplyItem(action=MessageAction(label="重新填 🔄", text="重新填 🔄")),
    ])
    return FlexMessage(alt_text="大叔記得你的口味", contents=bubble, quick_reply=qr)


def _build_taste_flex(full: list, partial: list, intros: dict) -> FlexMessage:
    """組裝個人化推薦的 Flex Message。full 為全符合，partial 為部分符合（score==3）。"""
    header = "大叔依你的口味找到了："
    contents = [
        FlexText(text=header, weight="bold", size="md", wrap=True),
    ]
    for s in full + partial:
        name = s["store_name"]
        dist = s["distance_km"]
        is_partial = s in partial
        maps_url = _persona.maps_url(name)
        intro = intros.get(name, "")
        contents.append(FlexSeparator(margin="lg"))
        contents.append(FlexText(text=name, weight="bold", size="md", margin="md", wrap=True))
        if is_partial:
            contents.append(FlexText(text="很接近，可以考慮", size="sm", color="#B07050", wrap=True))
        if intro:
            contents.append(FlexText(text=intro, size="sm", color="#888888", wrap=True))
        contents.append(FlexText(text=f"距你約 {dist} 公里", size="sm", color="#888888"))
        contents.append(FlexButton(
            action=URIAction(label="📍 地圖", uri=maps_url),
            style="primary",
            margin="md",
            height="sm",
        ))
    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    qr = QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="附近巷仔口 🏘️", text="附近巷仔口店家"))
    ])
    return FlexMessage(alt_text="大叔幫你找到了！", contents=bubble, quick_reply=qr)


@_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    if not NEARBY_SEARCH_ENABLED:
        return

    user_id = event.source.user_id
    matched_store = _get_session(user_id)

    if not matched_store:
        reply_text = "傳張照片給大叔看，大叔才知道你在找什麼路線！"
        reply_msg = TextMessage(text=reply_text)
    elif matched_store == _TASTE_SESSION:
        lat = event.message.latitude
        lng = event.message.longitude
        with _sessions_lock:
            entry = _sessions.get(user_id, {})
            answers = entry.get("taste_answers", {})
        _save_last_location(user_id, lat, lng)
        _clear_taste_quiz(user_id)
        candidates = _match_taste_stores(lat, lng, answers)
        full = [c for c in candidates if c["score"] == len(_TASTE_QUIZ_QUESTIONS)]
        partial = [c for c in candidates if c["score"] == len(_TASTE_QUIZ_QUESTIONS) - 1]
        if not candidates:
            reply_msg = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
        elif full:
            top_full = full[:3]
            intros = _generate_taste_intros(top_full)
            reply_msg = _build_taste_flex(top_full, [], intros)
        elif partial:
            top_partial = partial[:2]
            intros = _generate_taste_intros(top_partial)
            reply_msg = _build_taste_flex([], top_partial, intros)
        else:
            reply_msg = TextMessage(
                text="殘念！附近剛好沒有符合的店，換個地方再試試看？",
                quick_reply=QuickReply(items=[
                    QuickReplyItem(action=LocationAction(label="換個地方 📍"))
                ])
            )
    elif matched_store == _RANDOM_SESSION:
        if not _is_admin(user_id):
            logging.info("[event] random_surprise_triggered")
            _track("random_surprise")
        lat = event.message.latitude
        lng = event.message.longitude
        seen = _get_seen(user_id)
        expanded = _get_expanded(user_id)
        extended_km = 10.0 if expanded else 5.0
        reply_msg = None
        result = None
        open_pool = _get_open_pool()
        _CLOSED_MSG = "這時間大叔看了一圈，附近店家都已打烊了！"
        # exhausted = 目前有開的店在這個範圍內都已看過
        exhausted = search_random_nearby_store(lat, lng, open_pool, seen=seen, extended_radius_km=extended_km) is None
        if exhausted:
            if not expanded:
                # 先確認 5km 內有沒有任何店（不管打烊）
                has_any_total = search_random_nearby_store(lat, lng, _random_pool, seen=set()) is not None
                if not has_any_total:
                    # 5km 內根本沒有店
                    reply_msg = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
                else:
                    # 有店，再確認是打烊還是都看過
                    has_any_open = search_random_nearby_store(lat, lng, open_pool, seen=set()) is not None
                    if not has_any_open:
                        # 有店但全打烊
                        reply_msg = TextMessage(text=_CLOSED_MSG)
                    else:
                        # 有開著的店但都看過了，提示擴大範圍
                        _set_expanded(user_id, True)
                        reply_msg = TextMessage(text="大叔把5公里內的店都抽完了！要繼續擴大的話，再按一次隨機驚喜。")
            else:
                # 10km 也全部看過，重置
                _reset_seen(user_id)
                if len(seen) >= 10:
                    reply_msg = _build_exhausted_flex()
                else:
                    # 店少：確認 open_pool 是否有舊 seen 之外的新店
                    has_new = search_random_nearby_store(lat, lng, open_pool, seen=seen, primary_radius_km=extended_km, extended_radius_km=extended_km) is not None
                    if has_new:
                        # 有新店，用 seen=set() 保留允許重複推薦
                        result = search_random_nearby_store(lat, lng, open_pool, seen=set(), primary_radius_km=extended_km, extended_radius_km=extended_km)
                        if result is None:
                            reply_msg = TextMessage(text=_CLOSED_MSG)
                    else:
                        # open_pool 全在舊 seen 裡，避免無限循環
                        has_any_open = search_random_nearby_store(lat, lng, open_pool, seen=set(), primary_radius_km=extended_km, extended_radius_km=extended_km) is not None
                        if has_any_open:
                            reply_msg = TextMessage(text="這個時段附近有開的店都抽完了，換個時間再來試試！")
                        else:
                            reply_msg = TextMessage(text=_CLOSED_MSG)
        else:
            # 有開著的店且未全部看過，從 open_pool 內抽（flat pool）
            result = search_random_nearby_store(lat, lng, open_pool, seen=set(), primary_radius_km=extended_km, extended_radius_km=extended_km)
            if result is None:
                # open_pool 有店但抽不到（理論上不應發生）
                reply_msg = TextMessage(text=_CLOSED_MSG)
        if result:
            _add_to_seen(user_id, result["store_name"])
            reply_msg = _build_random_flex(result)
        elif reply_msg is None:
            reply_msg = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
    else:
        if not _is_admin(user_id):
            logging.info("[event] nearby_search_triggered")
            _track("nearby_search")
        lat = event.message.latitude
        lng = event.message.longitude
        results, any_in_radius = search_nearby_stores(matched_store, lat, lng, _store_notes)
        results_for_persona = sorted(results[:2], key=lambda x: x["distance_km"])
        if results_for_persona:
            reply_msg = _build_nearby_flex(results_for_persona)
        else:
            reply_msg = TextMessage(text=_persona.generate_nearby(matched_store, [], any_in_radius))

    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[reply_msg],
                )
            )
    except Exception:
        import traceback
        traceback.print_exc()


@_handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.show_loading_animation(
                ShowLoadingAnimationRequest(
                    chat_id=event.source.user_id,
                    loading_seconds=20,
                )
            )
    except Exception:
        pass

    threading.Thread(
        target=_process_image,
        args=(event.reply_token, event.message.id, event.source.user_id),
        daemon=True,
    ).start()


def _build_store_list_flex() -> FlexMessage:
    """動態從 store_notes.json 生成店家清單 Flex Message，按區分組。"""
    import re
    from collections import defaultdict

    # 按區分組
    district_stores: dict[str, list[str]] = defaultdict(list)
    for name in _store_notes.keys():
        m = re.search(r'[（(](.+?)[）)]', name)
        district = m.group(1) if m else "其他"
        district_stores[district].append(name)

    n = sum(len(v) for v in district_stores.values())

    rows = []
    for district, names in sorted(district_stores.items()):
        # 區標題
        rows.append(FlexText(
            text=district,
            size="xs",
            color="#aaaaaa",
            weight="bold",
            margin="md",
        ))
        for name in names:
            loc = _store_notes[name].get("location", {})
            lat = loc.get("lat")
            lng = loc.get("lng")
            map_uri = f"https://maps.google.com/?q={lat},{lng}" if lat and lng else f"https://maps.google.com/?q={name}"
            # 顯示名稱去掉區域後綴
            display_name = re.sub(r'[（(].+?[）)]$', '', name)
            rows.append(
                FlexBox(
                    layout="horizontal",
                    contents=[
                        FlexText(text=display_name, flex=1, size="md", weight="bold", wrap=True, gravity="center"),
                        FlexButton(
                            action=URIAction(label="📍", uri=map_uri),
                            flex=0,
                            height="sm",
                            style="link",
                        ),
                    ],
                    spacing="sm",
                )
            )

    header_text = f"目前收錄大台北 {n} 家店，準確率仍在優化中\n（魯肉飯真的都長太像了 XD）\n但已經可以玩玩看！"
    footer_text = "持續擴充中… 🍚\n\n💡 即使丟的店家不在收錄名單中，大叔仍會分析這碗魯肉飯/滷肉飯的風格，並從現有店家中找出相似風格的供參考。"

    bubble = FlexBubble(
        header=FlexBox(
            layout="vertical",
            contents=[FlexText(text=header_text, wrap=True, size="sm", color="#555555")],
            padding_all="lg",
        ),
        body=FlexBox(
            layout="vertical",
            contents=rows,
            spacing="sm",
            padding_all="lg",
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[FlexText(text=footer_text, wrap=True, size="xs", color="#888888")],
            padding_all="lg",
        ),
    )
    return FlexMessage(alt_text=f"收錄店家清單（{n} 家）", contents=bubble)


def _build_stats_message() -> TextMessage:
    """回傳 Firestore 統計數字（admin only）。"""
    if _db is None:
        return TextMessage(text="Firestore 未連線")
    try:
        from datetime import datetime, timedelta
        import zoneinfo
        tz = zoneinfo.ZoneInfo("Asia/Taipei")
        today = datetime.now(tz)
        today_key = today.strftime("%Y-%m-%d")
        # 本週一到今天
        week_start = today - timedelta(days=today.weekday())
        week_keys = [(week_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((today - week_start).days + 1)]

        def _sum_docs(keys):
            totals = {}
            for key in keys:
                doc = _db.collection("stats").document(key).get()
                if doc.exists:
                    for k, v in doc.to_dict().items():
                        totals[k] = totals.get(k, 0) + (v if isinstance(v, int) else 0)
            return totals

        total_doc = _db.collection("stats").document("events").get()
        total = total_doc.to_dict() if total_doc.exists else {}
        today_data = _sum_docs([today_key])
        week_data = _sum_docs(week_keys)

        def _fmt(d):
            img = d.get("image_received", 0)
            near = d.get("nearby_search", 0)
            rand = d.get("random_surprise", 0)
            personal = d.get("personal_recommendation", 0)
            return f"  丟照片：{img} 次\n  附近相似風格：{near} 次\n  隨機驚喜：{rand} 次\n  個人化：{personal} 次"

        districts = {k[len("district_"):]: v for k, v in total.items() if k.startswith("district_")}
        district_lines = "\n".join(
            f"  {k}：{v}" for k, v in sorted(districts.items(), key=lambda x: -x[1])
        ) or "（尚無資料）"

        text = (
            f"📊 使用統計\n\n"
            f"今天（{today_key}）\n{_fmt(today_data)}\n\n"
            f"本週（{week_keys[0]}–{today_key}）\n{_fmt(week_data)}\n\n"
            f"總計\n{_fmt(total)}\n\n"
            f"巷仔口各區（總計）\n{district_lines}"
        )
        return TextMessage(text=text)
    except Exception as e:
        return TextMessage(text=f"查詢失敗：{e}")


def _extract_district(store_name: str) -> str:
    """從店名括號中擷取區名，例如「路路食堂（林口區）」→「林口區」。取最後一個括號以避免「福哥（總店）（板橋區）」誤抓。"""
    import re
    matches = re.findall(r'[（(](.+?)[）)]', store_name)
    return matches[-1] if matches else "其他"


_TAIPEI_CITY_DISTRICTS = {"大安區", "文山區", "萬華區", "士林區", "中正區", "松山區", "信義區", "中山區", "內湖區", "南港區", "北投區"}

_QUICK_REPLY_ORDER = [
    "台北市區", "板橋區", "新莊區", "三重區",
    "永和區", "中和區", "新店區", "林口區", "五股區", "泰山區",
]


def _build_hidden_gems_quick_reply() -> QuickReply:
    """依 hidden_gems.json 動態產生 Quick Reply 選區按鈕，按 _QUICK_REPLY_ORDER 排序。"""
    available: set = set()
    for name in _hidden_gems.keys():
        d = _extract_district(name)
        if d in _TAIPEI_CITY_DISTRICTS:
            available.add("台北市區")
        else:
            available.add(d)

    ordered = [d for d in _QUICK_REPLY_ORDER if d in available]
    remaining = sorted(available - set(_QUICK_REPLY_ORDER))
    items = [
        QuickReplyItem(action=MessageAction(label=d, text=d))
        for d in ordered + remaining
    ]
    return QuickReply(items=items)


def _hidden_gems_districts() -> set:
    """回傳 hidden_gems.json 中所有區名集合（不含台北市各區，以「台北市區」代替）。"""
    districts = set()
    has_taipei = False
    for name in _hidden_gems.keys():
        d = _extract_district(name)
        if d in _TAIPEI_CITY_DISTRICTS:
            has_taipei = True
        else:
            districts.add(d)
    if has_taipei:
        districts.add("台北市區")
    return districts


def _build_taipei_city_flex() -> FlexMessage:
    """列出台北市各區（大安、文山、萬華、士林）店家，按區分組。"""
    import re
    rows = []
    _TAIPEI_CITY_ORDER = ["信義區", "大安區", "松山區", "中山區", "中正區", "萬華區", "士林區", "北投區", "南港區", "文山區", "內湖區"]
    for district in _TAIPEI_CITY_ORDER:
        stores = [(name, data) for name, data in _hidden_gems.items()
                  if _extract_district(name) == district]
        if not stores:
            continue
        if rows:
            rows.append(FlexSeparator(margin="lg", color="#B85A2B"))
        rows.append(FlexText(text=district, size="sm", weight="bold",
                             color="#B85A2B", margin="lg"))
        for i, (name, data) in enumerate(stores):
            loc = data.get("location", {})
            lat = loc.get("lat")
            lng = loc.get("lng")
            map_uri = (f"https://maps.google.com/?q={lat},{lng}"
                       if lat and lng else f"https://maps.google.com/?q={name}")
            display_name = re.sub(r'[（(].+?[）)]$', '', name)
            if i > 0:
                rows.append(FlexSeparator(margin="sm", color="#E6D9C8"))
            rows.append(
                FlexBox(
                    layout="horizontal",
                    contents=[
                        FlexText(text=display_name, flex=1, size="md", weight="bold",
                                 wrap=True, gravity="center", color="#333333"),
                        FlexButton(
                            action=URIAction(label="📍 地圖", uri=map_uri),
                            flex=0,
                            height="sm",
                            style="primary",
                            color="#A94E25",
                        ),
                    ],
                    spacing="md",
                    margin="sm",
                )
            )

    bubble = FlexBubble(
        header=FlexBox(
            layout="vertical",
            background_color="#B85A2B",
            padding_all="lg",
            contents=[
                FlexText(text="🛵  巷仔口", color="#FFE4B5", size="sm", weight="bold"),
                FlexText(text="台北市區", color="#FFFFFF", size="xxl", weight="bold"),
            ],
        ),
        body=FlexBox(
            layout="vertical",
            contents=rows,
            padding_all="lg",
            background_color="#F4EFE8",
        ),
        footer=FlexBox(
            layout="vertical",
            background_color="#F4EFE8",
            padding_all="md",
            contents=[
                FlexText(text="名單持續擴充中，歡迎推薦！",
                         wrap=True, size="xs", color="#8B6914", align="center"),
            ],
        ),
    )
    return FlexMessage(alt_text="巷仔口 · 台北市區", contents=bubble)


def _build_hidden_gems_flex(district: str) -> FlexMessage:
    """列出指定區的巷仔口店家 Flex Message，附地圖按鈕與 footer。"""
    import re
    stores = [(name, data) for name, data in _hidden_gems.items()
              if _extract_district(name) == district]

    rows = []
    for i, (name, data) in enumerate(stores):
        loc = data.get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")
        map_uri = (f"https://maps.google.com/?q={lat},{lng}"
                   if lat and lng else f"https://maps.google.com/?q={name}")
        display_name = re.sub(r'[（(].+?[）)]$', '', name)
        if i > 0:
            rows.append(FlexSeparator(margin="md", color="#E6D9C8"))
        rows.append(
            FlexBox(
                layout="horizontal",
                contents=[
                    FlexText(text=display_name, flex=1, size="md", weight="bold",
                             wrap=True, gravity="center", color="#333333"),
                    FlexButton(
                        action=URIAction(label="📍 地圖", uri=map_uri),
                        flex=0,
                        height="sm",
                        style="primary",
                        color="#A94E25",
                    ),
                ],
                spacing="md",
                margin="md" if i > 0 else "none",
            )
        )

    bubble = FlexBubble(
        header=FlexBox(
            layout="vertical",
            background_color="#B85A2B",
            padding_all="lg",
            contents=[
                FlexText(text="🛵  巷仔口", color="#FFE4B5", size="sm", weight="bold"),
                FlexText(text=district, color="#FFFFFF", size="xxl", weight="bold"),
            ],
        ),
        body=FlexBox(
            layout="vertical",
            contents=rows,
            padding_all="lg",
            background_color="#F4EFE8",
        ),
        footer=FlexBox(
            layout="vertical",
            background_color="#F4EFE8",
            padding_all="md",
            contents=[
                FlexText(text="名單持續擴充中，歡迎推薦！",
                         wrap=True, size="xs", color="#8B6914", align="center"),
            ],
        ),
    )
    return FlexMessage(alt_text=f"巷仔口 · {district}", contents=bubble)


def _nearby_hidden_gems(lat: float, lng: float, radius_km: float = 10.0) -> list:
    """回傳 radius_km 內的巷仔口店家，依距離排序。每筆為 (name, dist_km, is_open)。"""
    from src.nearby_search.searcher import haversine_km
    from datetime import datetime
    import zoneinfo
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei"))
    google_day = now.isoweekday() % 7
    current_hour = now.hour
    current_minute = now.minute
    result = []
    for name, data in _hidden_gems.items():
        loc = data.get("location")
        if not loc:
            continue
        dist = haversine_km(lat, lng, loc["lat"], loc["lng"])
        if dist > radius_km:
            continue
        hours_entry = _store_hours.get(name)
        if hours_entry and hours_entry.get("hours"):
            periods = hours_entry["hours"].get("periods", [])
            is_open = _is_currently_open(periods, google_day, current_hour, current_minute) if periods else True
        else:
            is_open = True  # 無資料一律視為營業中
        result.append((name, round(dist, 1), is_open))
    result.sort(key=lambda x: x[1])
    return result


def _build_nearby_hidden_gems_flex(gems: list) -> FlexMessage:
    """列出附近巷仔口店家的 Flex Message。每筆為 (name, dist_km, is_open)。"""
    contents = [
        FlexText(text="附近的巷仔口店家：", weight="bold", size="md", wrap=True),
    ]
    for name, dist, is_open in gems:
        loc = _hidden_gems.get(name, {}).get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")
        maps_url = f"https://maps.google.com/?q={lat},{lng}" if lat and lng else "https://maps.google.com/"
        contents.append(FlexSeparator(margin="lg"))
        display_name = name if is_open else f"{name}（目前打烊）"
        contents.append(FlexText(text=display_name, weight="bold", size="md", margin="md", wrap=True, color="#333333" if is_open else "#AAAAAA"))
        contents.append(FlexText(text=f"距你約 {dist} 公里", size="sm", color="#888888"))
        contents.append(FlexButton(
            action=URIAction(label="📍 地圖", uri=maps_url),
            style="primary" if is_open else "secondary",
            margin="md",
            height="sm",
        ))
    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    return FlexMessage(alt_text="附近巷仔口店家", contents=bubble)


def _radar_text() -> str:
    n = len(_store_notes)
    return f"""📡 大叔雷達：

1. 傳一張魯肉飯照片給大叔
2. 大叔評論完後，點下方「找附近類似的 📍」按鈕
3. 分享你的位置
4. 大叔雷達會幫你比對：
    肥肉派？還是瘦肉派？
    有沒有帶皮？
    醬汁是深色還是清爽？

幫你找附近風格相近的店 🗺️

5. 📌 大叔的承諾
大叔重視隱私，用戶分享的位置作為計算距離回傳推薦店家之用，並不做其他用途。

📍 目前收錄大台北 {n} 家店
（大叔還在努力吃更多店擴充中 😆）"""


_HOW_TO_USE_TEXT = """怎麼用：
1. 丟一張魯肉飯照片
📸 小提示：直接拍攝魯肉飯效果最佳，截圖或網路圖片辨識較不準。

2. 看大叔怎麼說
🧑‍🍳 小提示：大叔只看得懂魯肉飯，恕不陪聊😆（陪聊要算鐘點費XD

3. ⏳ 等待說明：
初次回應稍等幾秒暖機，之後就快了（但可能還是要幾秒～～被打）

4. 📌 大叔的承諾
大叔很健忘，看完就忘，照片不留存，放心傳、安心吃。

📩 有問題或回饋歡迎寫信🙏（大叔玻璃心，鞭小力）：ceasar0524@gmail.com

注意事項：
⚠️ 此工具為實驗性質，評論僅供參考
每個人口味不同，最重要的是找到屬於自己心中最愛的魯肉飯 🍚"""


def _text_reply_greeting() -> str:
    from datetime import datetime
    import zoneinfo
    hour = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei")).hour
    if 6 <= hour < 11:
        greeting = "這位同學早安！"
    elif 11 <= hour < 14:
        greeting = "這位同學午安！"
    elif 23 <= hour or hour < 6:
        greeting = "這位同學還沒睡？"
    else:
        greeting = "這位同學！"
    return f"{greeting}大叔只吃圖，不吃文字，請投餵一張魯肉飯照片 🍚"


def _taste_quiz_quick_reply(step: int) -> QuickReply:
    """回傳指定題次的 Quick Reply 按鈕。"""
    q = _TASTE_QUIZ_QUESTIONS[step]
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label=opt, text=opt))
        for opt in q["options"]
    ])


@_handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    text = event.message.text.strip() if event.message.text else ""
    user_id = event.source.user_id
    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            # 個人化問卷答案攔截（優先於其他關鍵字）
            quiz = _get_taste_quiz(user_id)
            if quiz is not None and text in _TASTE_QUIZ_ALL_OPTIONS:
                step = quiz["step"]
                answers = dict(quiz["answers"])
                q = _TASTE_QUIZ_QUESTIONS[step]
                answers[q["field"]] = q["mapping"][text]
                next_step = step + 1
                if next_step < len(_TASTE_QUIZ_QUESTIONS):
                    _save_taste_quiz(user_id, next_step, answers)
                    reply = TextMessage(
                        text=_TASTE_QUIZ_QUESTIONS[next_step]["question"],
                        quick_reply=_taste_quiz_quick_reply(next_step),
                    )
                else:
                    # 四題答完，詢問是否儲存偏好
                    _clear_taste_quiz(user_id)
                    _save_taste_save_pending(user_id, answers)
                    reply = TextMessage(
                        text="要儲存你的偏好嗎？下次可以直接用 🙌",
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(action=MessageAction(label="儲存 ✅", text="儲存 ✅")),
                            QuickReplyItem(action=MessageAction(label="不用 ❌", text="不用 ❌")),
                        ]),
                    )
            elif _get_taste_save_pending(user_id) is not None and text in ("儲存 ✅", "不用 ❌"):
                pending = _get_taste_save_pending(user_id)
                if text == "儲存 ✅":
                    _save_taste_preference(user_id, pending)
                _clear_taste_save_pending(user_id)
                _save_session(user_id, _TASTE_SESSION)
                with _sessions_lock:
                    if user_id in _sessions:
                        _sessions[user_id]["taste_answers"] = pending
                reply = TextMessage(
                    text="好！大叔幫你在附近找，分享一下你在哪 📍",
                    quick_reply=QuickReply(items=[
                        QuickReplyItem(action=LocationAction(label="分享位置 📍"))
                    ]),
                )
            elif _get_taste_loaded(user_id) is not None and text in ("直接用 ✅", "重新填 🔄"):
                if text == "直接用 ✅":
                    loaded = _get_taste_loaded(user_id)
                    _clear_taste_loaded(user_id)
                    _save_session(user_id, _TASTE_SESSION)
                    with _sessions_lock:
                        if user_id in _sessions:
                            _sessions[user_id]["taste_answers"] = loaded
                    reply = TextMessage(
                        text="好！大叔幫你在附近找，分享一下你在哪 📍",
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(action=LocationAction(label="分享位置 📍"))
                        ]),
                    )
                else:
                    _clear_taste_loaded(user_id)
                    _save_taste_quiz(user_id, 0, {})
                    reply = TextMessage(
                        text=_TASTE_QUIZ_QUESTIONS[0]["question"],
                        quick_reply=_taste_quiz_quick_reply(0),
                    )
            elif text == "統計" and _is_admin(event.source.user_id):
                reply = _build_stats_message()
            elif text == "怎麼用":
                reply = TextMessage(text=_HOW_TO_USE_TEXT)
            elif text == "店家清單":
                reply = _build_store_list_flex()
            elif text == "大叔雷達":
                reply = TextMessage(text=_radar_text())
            elif text == "巷仔口":
                if _hidden_gems:
                    reply = TextMessage(
                        text="選個區，大叔帶你逛巷仔口 🏘️",
                        quick_reply=_build_hidden_gems_quick_reply(),
                    )
                else:
                    reply = TextMessage(text="巷仔口名單還在整理中，敬請期待！")
            elif text == "附近巷仔口店家":
                last_loc = _get_last_location(user_id)
                if last_loc and _hidden_gems:
                    nearby = _nearby_hidden_gems(last_loc["lat"], last_loc["lng"], radius_km=3.0)
                    _clear_last_location(user_id)
                    if nearby:
                        reply = _build_nearby_hidden_gems_flex(nearby[:3])
                    else:
                        reply = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
                else:
                    reply = None
            elif text == "台北市區":
                reply = _build_taipei_city_flex()
            elif text in _hidden_gems_districts():
                reply = _build_hidden_gems_flex(text)
                if not _is_admin(event.source.user_id):
                    _track("district", f"district_{text}")
            elif text == "個人化":
                if not _is_admin(user_id):
                    _track("personal_recommendation")
                saved = _load_taste_preference(user_id)
                if saved:
                    _save_taste_loaded(user_id, saved)
                    reply = _build_taste_loaded_flex(saved)
                else:
                    _save_taste_quiz(user_id, 0, {})
                    reply = TextMessage(
                        text=_TASTE_QUIZ_QUESTIONS[0]["question"],
                        quick_reply=_taste_quiz_quick_reply(0),
                    )
            elif text == "隨機驚喜":
                _save_session(event.source.user_id, _RANDOM_SESSION)
                from datetime import datetime
                import zoneinfo
                _hour = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei")).hour
                if 6 <= _hour < 11:
                    _meal = "早餐"
                elif 11 <= _hour < 14:
                    _meal = "午餐"
                elif 14 <= _hour < 17:
                    _meal = "下午茶"
                elif 17 <= _hour < 21:
                    _meal = "晚餐"
                else:
                    _meal = "宵夜"
                reply = TextMessage(
                    text=f"大叔今天幫你決定{_meal}！分享位置讓大叔看看附近有啥 🎲",
                    quick_reply=QuickReply(items=[
                        QuickReplyItem(action=LocationAction(label="分享位置 📍"))
                    ]),
                )
            else:
                reply = TextMessage(text=_text_reply_greeting())
            if reply is not None:
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[reply],
                    )
                )
    except Exception:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
