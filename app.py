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
    PostbackAction,
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
    FlexFiller,
    FlexImage,
    FlexText,
    FlexSeparator,
    FlexCarousel,
    URIAction,
)
from linebot.v3.webhooks import ImageMessageContent, LocationMessageContent, MessageEvent, PostbackEvent, TextMessageContent

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

# 打卡足跡功能開關（設為 "false" 可快速關閉，不影響辨識流程）
CHECKIN_ENABLED = os.getenv("CHECKIN_ENABLED", "true").lower() == "true"

# 店家清單版面風格："michelin" 米其林指南風、"classic" 原始版
STORE_LIST_STYLE = "michelin"

# LIFF URL（在 LINE Developers Console 建立後填入）
RATINGS_LIFF_URL = os.getenv("RATINGS_LIFF_URL", "")
SHARE_LIFF_URL = os.getenv("SHARE_LIFF_URL", "")
SHARE_TASTE_LIFF_URL = os.getenv("SHARE_TASTE_LIFF_URL", "")

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

# 魯肉飯人格台詞對應表
# key: (fat_ratio, skin, sauce_consistency)，優先規則在 get_personality_tagline() 中處理
_GCS_ASSETS = "https://storage.googleapis.com/loo-bah-png-assets/personality"

_PERSONALITY_TAGLINES: dict = {
    ("fat_heavy", "with_skin",    "水"): ("在滷汁迷宮尋求黏嘴邂逅\n是否搞錯了什麼",         f"{_GCS_ASSETS}/maze.jpg"),
    ("fat_heavy", "with_skin",    "稠"): ("因為太思念那鍋濃稠滷汁而觸犯禁忌的我\n打開了魯肉飯的真相之門", f"{_GCS_ASSETS}/forbidden.jpg"),
    ("fat_heavy", "no_skin",      "水"): ("勇者喜歡巨滷有什麼錯！\n比起魔王我選擇肥肉正義",    f"{_GCS_ASSETS}/hero.jpg"),
    ("lean_heavy", "no_skin",     "水"): ("我也曾經以為魯肉飯一定要肥\n直到遇見那碗瘦瘦的你", f"{_GCS_ASSETS}/lean.jpg"),
    ("lean_heavy", "no_skin",     "稠"): ("明明沒有油花與膠質\n卻靠鹹香濃汁獨自升級成MAX",  f"{_GCS_ASSETS}/strongest.jpg"),
    ("lean_heavy", "with_skin",   "稠"): ("明明只想吃碗魯肉飯\n卻不小心踏上滷鼎雙修之路",    f"{_GCS_ASSETS}/dual.jpg"),
}
_TAGLINE_SWEET   = ("轉生成南部甜心的我\n今天也在滷鍋裡融化人心",         f"{_GCS_ASSETS}/sweet.jpg")
_TAGLINE_DEFAULT = ("一次意外，我竟成了\n魯肉飯新手村的大Boss", f"{_GCS_ASSETS}/boss.jpg")


def get_personality_tagline(answers: dict) -> tuple[str, str | None]:
    """依口味答案回傳 (台詞, 圖片URL|None)。優先順序：偏甜 > 全都可以 > 精確匹配 > fallback。"""
    fat    = answers.get("fat_ratio")
    skin   = answers.get("skin")
    sauce  = answers.get("sauce_consistency")
    taste  = answers.get("sauce_taste")
    if taste == "偏甜":
        return _TAGLINE_SWEET
    if fat is None and skin is None and sauce is None and taste is None:
        return _TAGLINE_DEFAULT
    result = _PERSONALITY_TAGLINES.get((fat, skin, sauce))
    return result if result else _TAGLINE_DEFAULT


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


def _save_taste_more(user_id: str, stores: list) -> None:
    """儲存個人化推薦剩餘店家，供「更多家」按鈕使用。"""
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["taste_more"] = stores
        _sessions[user_id]["ts"] = time.time()


def _get_taste_more(user_id: str) -> list | None:
    """回傳個人化推薦剩餘店家，若無則回傳 None。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        if time.time() - entry["ts"] > _SESSION_TTL:
            del _sessions[user_id]
            return None
        return entry.get("taste_more")


def _clear_taste_more(user_id: str) -> None:
    """清除個人化推薦剩餘店家。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("taste_more", None)


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


def _save_checkin_record(user_id: str, store_name: str, db_source: str) -> None:
    """非同步將打卡記錄寫入 Firestore user_footprint/<user_id>/records/。"""
    if _db is None:
        return
    def _write():
        from datetime import datetime, timezone
        try:
            _db.collection("user_footprint").document(user_id).collection("records").add({
                "store_name": store_name,
                "db": db_source,
                "checked_in_at": datetime.now(timezone.utc),
            })
        except Exception:
            pass
    threading.Thread(target=_write, daemon=True).start()


# ── 稱號系統 ──────────────────────────────────────────────────────────────────

_TITLE_THRESHOLDS = [
    ("魯肉飯大神", 60),
    ("魯肉飯勇者", 30),
    ("滷鍋守護者", 15),
    ("肉汁騎士",   5),
]
_TITLE_LEVEL_MAP = {
    "無職轉生者": 0,
    "肉汁騎士":   1,
    "滷鍋守護者": 2,
    "魯肉飯勇者": 3,
    "魯肉飯大神": 4,
}
_TITLE_NEXT = [
    ("肉汁騎士",   5),
    ("滷鍋守護者", 15),
    ("魯肉飯勇者", 30),
    ("魯肉飯大神", 60),
]
_UPGRADE_MESSAGES = {
    "肉汁騎士":   [
        "🗡️ 晉升【{display}】！你已經不是普通人了，繼續衝！",
        "🗡️ 哎唷，【{display}】出現了！魯肉飯之路才剛開始！",
    ],
    "滷鍋守護者": [
        "🛡️ 晉升【{display}】！你守護的不只是滷鍋，是台灣魂！",
        "🛡️ 夭壽喔，【{display}】！你已經半個魯肉飯專家了！",
    ],
    "魯肉飯勇者": [
        "⚔️ 晉升【{display}】！勇者就位，魯肉飯江湖震動！",
        "⚔️ 哇賽，【{display}】！大叔要向你鞠躬了！",
    ],
    "魯肉飯大神": [
        "👑 晉升【{display}】！神蹟降臨，台北魯肉飯江湖從此有你的傳說！",
        "👑 嘖嘖嘖，【{display}】！大叔活到這個歲數，終於等到你了！",
    ],
}


_TITLE_EMOJIS = {
    "肉汁騎士":   "🗡️",
    "滷鍋守護者": "🛡️",
    "魯肉飯勇者": "⚔️",
    "魯肉飯大神": "👑",
}


def _build_progress_flex(unique_count: int) -> FlexMessage | None:
    """組裝打卡進度條 Flex Message，顯示距離下一個稱號的進度。已是最高稱號回傳 None。"""
    next_title = None
    threshold = None
    for t, n in _TITLE_NEXT:
        if unique_count < n:
            next_title = t
            threshold = n
            break
    if next_title is None:
        return None

    filled = int(unique_count / threshold * 10)
    filled = max(0, min(10, filled))
    empty = 10 - filled
    bar = "█" * filled + "░" * empty

    next_level = _TITLE_LEVEL_MAP.get(next_title, 0)

    body_contents = [
        FlexText(text=f"即將解鎖｜Lv.{next_level} {next_title}", size="sm", color="#9A4F12", weight="bold", margin="none"),
        FlexBox(
            layout="horizontal",
            margin="md",
            align_items="center",
            contents=[
                FlexBox(
                    layout="horizontal",
                    flex=filled if filled > 0 else 0,
                    height="12px",
                    background_color="#9A4F12",
                    corner_radius="4px",
                    contents=[FlexFiller()],
                ) if filled > 0 else FlexFiller(),
                FlexBox(
                    layout="horizontal",
                    flex=empty if empty > 0 else 0,
                    height="12px",
                    background_color="#D8B894",
                    corner_radius="4px",
                    contents=[FlexFiller()],
                ) if empty > 0 else FlexFiller(),
            ],
        ),
        FlexBox(
            layout="horizontal",
            margin="sm",
            contents=[
                FlexText(text=f"{unique_count} / {threshold} 家", size="xs", color="#4A2A16", flex=1),
                FlexText(text=f"🔥 再 {threshold - unique_count} 家升級！", size="sm", color="#D85A1F", align="end"),
            ],
        ),
    ]

    bubble = FlexBubble(
        body=FlexBox(
            layout="vertical",
            contents=body_contents,
            padding_all="lg",
        ),
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#FFF7EA"),
        ),
    )
    return FlexMessage(alt_text=f"{next_title} 進度 {unique_count}/{threshold}", contents=bubble)


def _build_upgrade_flex(old_title: str, new_title: str, display: str, message: str) -> FlexMessage:
    """組裝 RPG 風格升級 Flex Message。"""
    emoji = _TITLE_EMOJIS.get(new_title, "🎉")
    old_label = old_title or "無職轉生者"

    header = FlexBox(
        layout="vertical",
        background_color="#1A1A2E",
        padding_all="lg",
        contents=[
            FlexText(text="✦ 稱號解鎖 ✦", weight="bold", size="sm", color="#FFD700", align="center"),
            FlexText(
                text=f"{old_label}  →  {new_title}",
                size="xs", color="#AAAAAA", align="center", margin="sm",
            ),
        ],
    )

    body = FlexBox(
        layout="vertical",
        padding_all="xl",
        contents=[
            FlexText(text=emoji, size="5xl", align="center"),
            FlexText(text=new_title, weight="bold", size="xxl", color="#FFD700", align="center", margin="md"),
            FlexText(text=f"#{display.split('#')[-1]}", size="sm", color="#AAAAAA", align="center", margin="xs"),
            FlexSeparator(margin="lg"),
            FlexText(text=message, size="sm", color="#CCCCCC", wrap=True, align="center", margin="lg"),
        ],
    )

    bubble = FlexBubble(
        header=header,
        body=body,
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#16213E"),
        ),
    )
    return FlexMessage(alt_text=f"稱號解鎖：{new_title}", contents=bubble)


_TITLE_CERTIFICATIONS = {
    "無職轉生者": "初踏江湖，年輕人終究是年輕人！",
    "肉汁騎士":   "年紀輕輕就有坐騎，前途無量！",
    "滷鍋守護者": "魯肉飯是你的摯愛，你甘願為它赴湯蹈火",
    "魯肉飯勇者": "身經百戰，一碗魯肉飯的好壞騙不了你",
    "魯肉飯大神": "這世界居然有人自稱為大神，大叔甘拜下風🙇",
}


def _build_title_flex(display: str, current_title: str, unique_count: int) -> FlexMessage:
    """組裝稱號查詢 Flex Message。"""
    certification = _TITLE_CERTIFICATIONS.get(current_title, "")

    next_info = ""
    for next_title, threshold in _TITLE_NEXT:
        if unique_count < threshold:
            next_info = f"再吃 {threshold - unique_count} 家升級{next_title}！"
            break

    header = FlexBox(
        layout="vertical",
        background_color="#4B2F24",
        padding_all="lg",
        contents=[
            FlexText(text="🏅 " + current_title, weight="bold", size="xl", color="#FFD700"),
            FlexText(text=display, size="sm", color="#FFD700", margin="xs"),
        ],
    )

    body_contents = [
        FlexText(text="🍚", size="5xl", align="center", margin="lg"),
        FlexSeparator(margin="lg"),
        FlexText(
            text=f"你已解鎖 {unique_count} / 110 家",
            weight="bold", size="md", align="center", margin="lg", color="#4B2F24",
        ),
        FlexText(
            text=f"大叔認證：{certification}",
            size="sm", color="#888888", wrap=True, align="center", margin="sm",
        ),
    ]
    if next_info:
        body_contents.append(FlexText(
            text=next_info,
            size="sm", color="#B85A2B", wrap=True, align="center", margin="md", weight="bold",
        ))

    bubble = FlexBubble(
        header=header,
        body=FlexBox(
            layout="vertical",
            contents=body_contents,
            padding_all="lg",
        ),
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#F9F5F0"),
        ),
    )
    return FlexMessage(alt_text=f"稱號：{display}", contents=bubble)


def _get_title(unique_count: int) -> str:
    """依唯一打卡店家數回傳對應稱號。"""
    for title, threshold in _TITLE_THRESHOLDS:
        if unique_count >= threshold:
            return title
    return "無職轉生者"


def _get_title_number(user_id: str, title: str) -> str:
    """產生稱號代號。無職轉生者用 user_id 後4碼，其餘用流水號-後4碼格式（如 1-a3f9）。"""
    suffix = user_id[-4:]
    if title == "無職轉生者":
        return suffix
    if _db is None:
        return f"1-{suffix}"
    try:
        counter_ref = _db.collection("title_counter").document(title)
        transaction = _db.transaction()

        @_firestore.transactional
        def _increment(txn, ref):
            snap = ref.get(transaction=txn)
            count = ((snap.to_dict() or {}).get("count") or 0) + 1
            txn.set(ref, {"count": count})
            return count

        count = _increment(transaction, counter_ref)
        return f"{count}-{suffix}"
    except Exception:
        return f"1-{suffix}"


def _build_rating_prompt(store_name: str) -> TextMessage:
    """組裝打卡後的評價邀請訊息。"""
    return TextMessage(
        text="這家怎麼樣？",
        quick_reply=QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="必吃 👍", text="必吃 👍")),
            QuickReplyItem(action=MessageAction(label="普通 😐", text="普通 😐")),
            QuickReplyItem(action=MessageAction(label="不能只有我吃到 🤫", text="不能只有我吃到 🤫")),
        ]),
    )


def _get_revisit_tagline(visit_count: int) -> str:
    """依回訪次數回傳台詞，首次打卡（visit_count==1）回傳空字串。"""
    if visit_count <= 1:
        return ""
    n = visit_count
    if n == 2:
        return f"第 {n} 次回訪，這碗有什麼魔力"
    elif n == 3:
        return f"第 {n} 次回訪，好吃到吃不膩耶！"
    elif n == 4:
        return f"第 {n} 次回訪，這家是有多好吃啦，大叔都心動了"
    elif n <= 7:
        return f"第 {n} 次回訪，大叔懷疑你家就住這附近"
    elif n <= 9:
        return f"第 {n} 次回訪，老實說，你是不是股東？"
    else:
        return f"第 {n} 次回訪，太猛啦～根本十里坡滷神，大叔甘拜下風！"


def _process_checkin_with_title(user_id: str, store_name: str, db_source: str) -> list:
    """處理打卡並偵測稱號升級。回傳訊息列表（打卡確認 + 可能的升級儀式 + 評價邀請）。"""
    import random as _random
    confirm_msg = TextMessage(text=f"「{store_name}」打卡成功！大叔幫你記下來了 🍚")
    _save_pending_rating(user_id, store_name)
    rating_msg = _build_rating_prompt(store_name)

    if _db is None:
        _save_checkin_record(user_id, store_name, db_source)
        return [confirm_msg, rating_msg]

    try:
        records_ref = _db.collection("user_footprint").document(user_id).collection("records")
        existing_docs = list(records_ref.stream())
        existing_stores = {d.to_dict().get("store_name") for d in existing_docs}
        existing_stores.add(store_name)
        unique_count = len(existing_stores)

        visit_count = sum(1 for d in existing_docs if d.to_dict().get("store_name") == store_name) + 1
        revisit_tagline = _get_revisit_tagline(visit_count)
        if revisit_tagline:
            confirm_msg = TextMessage(text=f"「{store_name}」打卡成功！{revisit_tagline} 🍚")

        user_doc = _db.collection("user_footprint").document(user_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}
        current_title = user_data.get("current_title")

        new_title = _get_title(unique_count)
        needs_update = current_title != new_title
        is_ceremony = needs_update and new_title != "無職轉生者"

        _save_checkin_record(user_id, store_name, db_source)

        if needs_update:
            title_number = _get_title_number(user_id, new_title)

            def _update():
                try:
                    _db.collection("user_footprint").document(user_id).set(
                        {"current_title": new_title, "title_number": title_number},
                        merge=True,
                    )
                except Exception:
                    pass

            threading.Thread(target=_update, daemon=True).start()
        else:
            title_number = user_data.get("title_number") or user_id[-4:]

        if is_ceremony:
            display = f"{new_title}#{title_number}"
            templates = _UPGRADE_MESSAGES.get(new_title, ["🎉 恭喜晉升！"])
            text = _random.choice(templates).format(display=display)
            upgrade_flex = _build_upgrade_flex(current_title, new_title, display, text)
            progress_flex = _build_progress_flex(unique_count)
            msgs = [confirm_msg, upgrade_flex]
            if progress_flex:
                msgs.append(progress_flex)
            msgs.append(rating_msg)
            return msgs

        progress_flex = _build_progress_flex(unique_count)
        if progress_flex:
            return [confirm_msg, progress_flex, rating_msg]

    except Exception:
        import traceback
        traceback.print_exc()
        _save_checkin_record(user_id, store_name, db_source)

    return [confirm_msg, rating_msg]


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


# ── pending_checkin session helpers ──────────────────────────────────────────

def _save_pending_checkin(user_id: str, store_name: str, db_source: str) -> None:
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["pending_checkin"] = {"store": store_name, "db": db_source}
        _sessions[user_id]["ts"] = time.time()


def _get_pending_checkin(user_id: str) -> dict | None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        return entry.get("pending_checkin")


def _clear_pending_checkin(user_id: str) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("pending_checkin", None)


# ── checkin_rescue session helpers ───────────────────────────────────────────

def _set_checkin_rescue(user_id: str) -> None:
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["checkin_rescue"] = True
        _sessions[user_id]["ts"] = time.time()


def _get_checkin_rescue(user_id: str) -> bool:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return False
        return bool(entry.get("checkin_rescue"))


def _clear_checkin_rescue(user_id: str) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("checkin_rescue", None)
            entry.pop("rescue_stores", None)


def _save_rescue_stores(user_id: str, stores: dict) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry["rescue_stores"] = stores
            entry["ts"] = time.time()


def _get_rescue_stores(user_id: str) -> dict | None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        return entry.get("rescue_stores")


def _clear_rescue_stores(user_id: str) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("rescue_stores", None)


# ── pending_rating session helpers ───────────────────────────────────────────

def _save_pending_rating(user_id: str, store_name: str) -> None:
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {"store": None, "ts": time.time(), "seen": set()}
        _sessions[user_id]["pending_rating"] = store_name
        _sessions[user_id]["ts"] = time.time()


def _get_pending_rating(user_id: str) -> str | None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        return entry.get("pending_rating")


def _clear_pending_rating(user_id: str) -> None:
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is not None:
            entry.pop("pending_rating", None)


def _save_rating_record(user_id: str, store_name: str, rating: str) -> None:
    """非同步寫入評價記錄至 store_ratings/<store_name>/votes/<user_id>。"""
    if _db is None:
        return

    def _write():
        try:
            from datetime import datetime, timezone
            user_doc = _db.collection("user_footprint").document(user_id).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            title = user_data.get("current_title") or "無職轉生者"
            title_number = user_data.get("title_number") or user_id[-4:]
            _db.collection("store_ratings").document(store_name).collection("votes").document(user_id).set({
                "rating": rating,
                "rated_at": datetime.now(timezone.utc),
                "title": title,
                "title_number": title_number,
            })
        except Exception:
            pass

    threading.Thread(target=_write, daemon=True).start()


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


@app.route("/api/ratings/<path:store_name>", methods=["GET"])
def api_ratings(store_name):
    """回傳指定店家的所有評價代號清單，依稱號等級排序。"""
    if _db is None:
        return {"votes": []}, 200
    try:
        _TITLE_RANK = {"魯肉飯大神": 4, "魯肉飯勇者": 3, "滷鍋守護者": 2, "肉汁騎士": 1, "無職轉生者": 0}
        _RATING_LABEL = {"must_eat": "說必吃！🔥", "neutral": "說普通 😐", "bad": "說不能只有我吃到 🤫"}
        votes_ref = _db.collection("store_ratings").document(store_name).collection("votes")
        docs = votes_ref.stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            user_id = doc.id
            user_doc = _db.collection("user_footprint").document(user_id).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            title = user_data.get("current_title") or d.get("title", "無職轉生者")
            title_number = user_data.get("title_number") or d.get("title_number", "")
            rating = d.get("rating", "neutral")
            label = _RATING_LABEL.get(rating, "說普通 😐")
            results.append({"display": f"{title}#{title_number} {label}", "rank": _TITLE_RANK.get(title, 0)})
        results.sort(key=lambda x: x["rank"], reverse=True)
        return {"votes": [r["display"] for r in results]}, 200
    except Exception:
        return {"votes": []}, 200


@app.route("/api/user-title", methods=["GET"])
def api_user_title():
    """用 LIFF access token 查詢用戶稱號。"""
    import urllib.request as _urllib_req
    import json as _json
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return {"error": "unauthorized"}, 401
    access_token = auth[7:]
    try:
        req = _urllib_req.Request(
            "https://api.line.me/v2/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with _urllib_req.urlopen(req, timeout=5) as resp:
            profile = _json.loads(resp.read().decode())
        user_id = profile.get("userId", "")
        if not user_id:
            return {"error": "invalid token"}, 401
        if _db is None:
            suffix = user_id[-4:]
            return {"title": "無職轉生者", "title_number": suffix, "display": f"無職轉生者#{suffix}"}, 200
        user_doc = _db.collection("user_footprint").document(user_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}
        title = user_data.get("current_title") or "無職轉生者"
        title_number = user_data.get("title_number") or user_id[-4:]
        return {"title": title, "title_number": title_number, "display": f"{title}#{title_number}"}, 200
    except Exception:
        return {"error": "server error"}, 500


@app.route("/liff/ratings", methods=["GET"])
def liff_ratings():
    """LIFF 評價展示頁：彈幕式展示 must_eat 評價代號。"""
    store = request.args.get("store", "")
    liff_id = os.getenv("RATINGS_LIFF_ID", "")
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>同好評價</title>
<script src="https://static.line-scdn.net/liff/edge/versions/2.22.3/sdk.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #1A1A2E; color: #FFD700; font-family: sans-serif; overflow: hidden; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
h2 {{ font-size: 1.1rem; margin-bottom: 1rem; color: #FFD700; }}
.store-name {{ font-size: 1.4rem; font-weight: bold; margin-bottom: 1.5rem; color: #fff; }}
.danmaku-container {{ width: 100%; height: 60vh; position: relative; overflow: hidden; }}
.danmaku-item {{ position: absolute; white-space: nowrap; font-size: 1rem; font-weight: bold; color: #FFD700; animation: scroll linear forwards; opacity: 0.9; }}
@keyframes scroll {{ from {{ right: -300px; }} to {{ right: 110%; }} }}
.empty {{ font-size: 1rem; color: #AAAAAA; text-align: center; padding: 2rem; }}
</style>
</head>
<body>
<h2>🔥 同好推薦</h2>
<div class="store-name" id="storeName"></div>
<div class="danmaku-container" id="danmaku"></div>
<div class="empty" id="emptyMsg" style="display:none">還沒有人評價，你來當第一個！</div>
<script>
function getParam(url, key) {{
  const re = new RegExp("[?&]" + key.replace(".", "\\.") + "=([^&]+)");
  const m = url.match(re);
  return m ? decodeURIComponent(m[1]) : "";
}}
liff.init({{ liffId: "{liff_id}" }}).then(() => {{
  const href = window.location.href;
  let store = getParam(href, "store");
  if (!store) {{
    const rawState = getParam(href, "liff.state");
    if (rawState) store = getParam(decodeURIComponent(rawState), "store");
  }}
  document.getElementById("storeName").textContent = store;
  if (!store) {{
    document.getElementById("emptyMsg").style.display = "block";
    return;
  }}
  fetch("/api/ratings/" + encodeURIComponent(store))
    .then(r => r.json())
    .then(data => {{
      const votes = data.votes || [];
      if (votes.length === 0) {{
        document.getElementById("emptyMsg").style.display = "block";
        return;
      }}
      const container = document.getElementById("danmaku");
      const shoot = () => {{
        const idx = Math.floor(Math.random() * votes.length);
        const el = document.createElement("div");
        el.className = "danmaku-item";
        el.textContent = votes[idx];
        el.style.top = Math.random() * 80 + "%";
        const dur = 4 + Math.random() * 4;
        el.style.animation = `scroll ${{dur}}s linear forwards`;
        container.appendChild(el);
        setTimeout(() => el.remove(), dur * 1000);
      }};
      shoot();
      setInterval(shoot, 1200);
    }});
}}).catch(() => {{
  document.getElementById("emptyMsg").style.display = "block";
}});
</script>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/liff/share", methods=["GET"])
def liff_share():
    """LIFF 分享頁：立即呼叫 shareTargetPicker 發送店家 Flex Message。"""
    liff_id = os.getenv("SHARE_LIFF_ID", "")
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>分享店家</title>
<script src="https://static.line-scdn.net/liff/edge/versions/2.22.3/sdk.js"></script>
<style>
body {{ background: #1A1A2E; color: #FFD700; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; }}
p {{ color: #AAAAAA; font-size: 0.9rem; }}
</style>
</head>
<body>
<p>準備分享中⋯</p>
<script>
function getShareParam(url, key) {{
  const re = new RegExp("[?&]" + key.replace(".", "\\.") + "=([^&]+)");
  const m = url.match(re);
  return m ? decodeURIComponent(m[1]) : "";
}}
liff.init({{ liffId: "{liff_id}" }}).then(() => {{
  const href = window.location.href;
  let store = getShareParam(href, "store");
  let lat = getShareParam(href, "lat");
  let lng = getShareParam(href, "lng");
  let tagline = getShareParam(href, "tagline");
  if (!store) {{
    const rawState = getShareParam(href, "liff\\.state");
    if (rawState) {{
      const decoded = decodeURIComponent(rawState);
      store = getShareParam(decoded, "store");
      lat = getShareParam(decoded, "lat");
      lng = getShareParam(decoded, "lng");
      tagline = getShareParam(decoded, "tagline");
    }}
  }}
  const mapsUrl = (lat && lng) ? "https://maps.google.com/?q=" + lat + "," + lng : "https://maps.google.com/";
  if (!store) {{
    document.querySelector("p").textContent = "找不到店家資訊";
    return;
  }}
  return fetch("/api/user-title", {{
    headers: {{ "Authorization": "Bearer " + liff.getAccessToken() }}
  }}).then(r => r.ok ? r.json() : {{}}).catch(() => ({{}})).then(data => {{
    const display = data.display || "";
    const bubbleContents = [];
    if (tagline) {{
      bubbleContents.push({{
        type: "bubble",
        header: {{
          type: "box", layout: "vertical", backgroundColor: "#4B2F24", paddingAll: "lg",
          contents: [{{ type: "text", text: "🎲 隨機驚喜", weight: "bold", color: "#FFFFFF", size: "md" }}]
        }},
        body: {{
          type: "box", layout: "vertical", paddingAll: "lg",
          contents: [
            {{ type: "text", text: "📜  " + tagline, weight: "bold", size: "lg", color: "#8B4513", wrap: true, align: "center" }},
            {{ type: "separator", margin: "lg" }},
            {{ type: "text", text: store, weight: "bold", size: "xl", wrap: true, color: "#4B2F24", margin: "lg" }},
            ...(display ? [{{ type: "text", text: display + " 抽到這家！", size: "sm", color: "#B85A2B", margin: "sm", wrap: true }}] : []),
            {{ type: "button", action: {{ type: "uri", label: "📍 地圖", uri: mapsUrl }}, style: "primary", margin: "md", height: "sm" }},
            {{ type: "button", action: {{ type: "uri", label: "🤖 加入魯肉飯大叔", uri: "https://line.me/R/ti/p/%40940srtss" }}, style: "secondary", margin: "sm", height: "sm" }}
          ]
        }}
      }});
    }} else {{
      const bodyContents = [
        {{ type: "text", text: store, weight: "bold", size: "xl", wrap: true, color: "#4B2F24" }}
      ];
      if (display) {{
        bodyContents.push({{ type: "text", text: display + " 推薦這家！", size: "sm", color: "#B85A2B", margin: "sm", wrap: true }});
      }}
      bodyContents.push({{ type: "button", action: {{ type: "uri", label: "📍 地圖", uri: mapsUrl }}, style: "primary", margin: "md", height: "sm" }});
      bodyContents.push({{ type: "button", action: {{ type: "uri", label: "🤖 加入魯肉飯大叔", uri: "https://line.me/R/ti/p/%40940srtss" }}, style: "secondary", margin: "sm", height: "sm" }});
      bubbleContents.push({{
        type: "bubble",
        header: {{
          type: "box", layout: "vertical", backgroundColor: "#4B2F24", paddingAll: "lg",
          contents: [{{ type: "text", text: "🍚 同好推薦", weight: "bold", color: "#FFFFFF", size: "md" }}]
        }},
        body: {{
          type: "box", layout: "vertical", paddingAll: "lg",
          contents: bodyContents
        }}
      }});
    }}
    return liff.shareTargetPicker([{{
      type: "flex",
      altText: tagline ? "📜 " + tagline.split("\\n")[0] + "（" + store + "）" : (display ? display + " 推薦：" : "🍚 同好推薦：") + store,
      contents: bubbleContents[0]
    }}]);
  }});
}}).then(() => liff.closeWindow()).catch(err => {{
  document.querySelector("p").textContent = "錯誤：" + (err && err.message || JSON.stringify(err));
}});
</script>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/liff/share-taste", methods=["GET"])
def liff_share_taste():
    """LIFF 分享頁：分享個人口味人格台詞。"""
    liff_id = os.getenv("SHARE_TASTE_LIFF_ID", "")
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>分享口味</title>
<script src="https://static.line-scdn.net/liff/edge/versions/2.22.3/sdk.js"></script>
<style>
body {{ background: #1A1A2E; color: #FFD700; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; }}
p {{ color: #AAAAAA; font-size: 0.9rem; }}
</style>
</head>
<body>
<p>準備分享中⋯</p>
<script>
function getParam(url, key) {{
  const re = new RegExp("[?&]" + key.replace(".", "\\.") + "=([^&]+)");
  const m = url.match(re);
  return m ? decodeURIComponent(m[1]) : "";
}}
function extractParams(href) {{
  let tagline = getParam(href, "tagline");
  let img     = getParam(href, "img");
  let fat     = getParam(href, "fat");
  let skin    = getParam(href, "skin");
  let sauce   = getParam(href, "sauce");
  let taste   = getParam(href, "taste");
  if (!tagline) {{
    const rawState = getParam(href, "liff\\.state");
    if (rawState) {{
      const decoded = decodeURIComponent(rawState);
      tagline = getParam(decoded, "tagline");
      img     = getParam(decoded, "img");
      fat     = getParam(decoded, "fat");
      skin    = getParam(decoded, "skin");
      sauce   = getParam(decoded, "sauce");
      taste   = getParam(decoded, "taste");
    }}
  }}
  return {{ tagline, img, fat, skin, sauce, taste }};
}}
liff.init({{ liffId: "{liff_id}" }}).then(() => {{
  const p = extractParams(window.location.href);
  if (!p.tagline) {{
    document.querySelector("p").textContent = "找不到口味資訊";
    return;
  }}
  const tasteRows = [];
  if (p.fat)   tasteRows.push({{ type: "text", text: "🍖  " + p.fat,   size: "lg", weight: "bold", color: "#4B2F24" }});
  if (p.skin)  tasteRows.push({{ type: "text", text: "💋  " + p.skin,  size: "lg", weight: "bold", color: "#4B2F24", margin: "md" }});
  if (p.sauce) tasteRows.push({{ type: "text", text: "🍯  " + p.sauce, size: "lg", weight: "bold", color: "#4B2F24", margin: "md" }});
  if (p.taste) tasteRows.push({{ type: "text", text: "🧂  " + p.taste, size: "lg", weight: "bold", color: "#4B2F24", margin: "md" }});
  tasteRows.push({{ type: "separator", margin: "lg" }});
  tasteRows.push({{ type: "button", action: {{ type: "uri", label: "🤖 加入魯肉飯大叔", uri: "https://line.me/R/ti/p/%40940srtss" }}, style: "secondary", margin: "md", height: "sm" }});
  const taglineLines = p.tagline.split("\\n");
  const line1 = "✦ " + taglineLines[0];
  const line2 = taglineLines[1] || "";
  const headerContents = [
    {{ type: "text", text: line1, weight: "bold", size: "lg", color: "#FFFFFF", wrap: true }}
  ];
  if (line2) {{
    headerContents.push({{ type: "text", text: line2, size: "sm", color: "#FFFFFF", align: "end", wrap: true, margin: "sm" }});
  }}
  const bubble = {{
    type: "bubble",
    hero: p.img ? {{ type: "image", url: p.img, size: "full", aspectRatio: "20:13", aspectMode: "cover" }} : undefined,
    header: {{
      type: "box", layout: "vertical", backgroundColor: "#6A3F2D", paddingAll: "lg",
      contents: headerContents
    }},
    body: {{
      type: "box", layout: "vertical", paddingAll: "lg", backgroundColor: "#E9E1D8",
      contents: tasteRows
    }}
  }};
  return liff.shareTargetPicker([{{
    type: "flex",
    altText: p.tagline.split("\\n")[0],
    contents: bubble
  }}]);
}}).then(() => liff.closeWindow()).catch(err => {{
  document.querySelector("p").textContent = "錯誤：" + (err && err.message || JSON.stringify(err));
}});
</script>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


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
        reply_text, matched_store, is_lu_rou_fan = pipeline_run(tmp_path, index_path="index.npz")
    except Exception:
        import traceback
        traceback.print_exc()
        reply_text = "大叔出去買魯肉飯，等一下！再試一次啦！"
        matched_store = None
        is_lu_rou_fan = False
    finally:
        os.unlink(tmp_path)

    if not _is_admin(user_id) and matched_store:
        logging.info("[event] recognition_success store=%s", matched_store)

    if NEARBY_SEARCH_ENABLED and matched_store:
        _save_session(user_id, matched_store)

    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            qr_items = []
            if matched_store:
                if CHECKIN_ENABLED:
                    _save_pending_checkin(user_id, matched_store, "store_notes")
                    qr_items.append(QuickReplyItem(action=MessageAction(label=f"✅ {matched_store}", text="就是這家 ✅")))
                    qr_items.append(QuickReplyItem(action=MessageAction(label="打卡這碗 📍", text="打卡這碗 📍")))
                elif NEARBY_SEARCH_ENABLED:
                    qr_items.append(QuickReplyItem(action=LocationAction(label="找附近類似的 📍")))
            elif CHECKIN_ENABLED and is_lu_rou_fan:
                qr_items.append(QuickReplyItem(action=MessageAction(label="打卡這碗 📍", text="打卡這碗 📍")))
            if qr_items:
                msg = TextMessage(text=reply_text, quick_reply=QuickReply(items=qr_items))
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


def _get_must_eat_count(store_name: str) -> int:
    """讀取 store_ratings/<store_name>/votes 中 must_eat 票數。"""
    if _db is None:
        return 0
    try:
        votes = _db.collection("store_ratings").document(store_name).collection("votes").where("rating", "==", "must_eat").stream()
        return sum(1 for _ in votes)
    except Exception:
        return 0


def _run_random_surprise(user_id: str, lat: float, lng: float):
    """隨機驚喜核心邏輯，回傳 reply_msg。供位置事件與「下一抽」共用。"""
    seen = _get_seen(user_id)
    expanded = _get_expanded(user_id)
    extended_km = 7.0 if expanded else 3.0
    reply_msg = None
    result = None
    open_pool = _get_open_pool()
    _CLOSED_MSG = "這時間大叔看了一圈，附近店家都已打烊了！"
    exhausted = search_random_nearby_store(lat, lng, open_pool, seen=seen, extended_radius_km=extended_km) is None
    if exhausted:
        if not expanded:
            has_any_total = search_random_nearby_store(lat, lng, _random_pool, seen=set(), extended_radius_km=3.0) is not None
            if not has_any_total:
                reply_msg = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
            else:
                has_any_open = search_random_nearby_store(lat, lng, open_pool, seen=set(), extended_radius_km=3.0) is not None
                if not has_any_open:
                    reply_msg = TextMessage(text=_CLOSED_MSG)
                else:
                    _set_expanded(user_id, True)
                    reply_msg = TextMessage(text="大叔把3公里內的店都抽完了！要繼續擴大的話，再按一次隨機驚喜。")
        else:
            _reset_seen(user_id)
            if len(seen) >= 10:
                reply_msg = _build_exhausted_flex()
            else:
                has_new = search_random_nearby_store(lat, lng, open_pool, seen=seen, primary_radius_km=extended_km, extended_radius_km=extended_km) is not None
                if has_new:
                    result = search_random_nearby_store(lat, lng, open_pool, seen=set(), primary_radius_km=extended_km, extended_radius_km=extended_km)
                    if result is None:
                        reply_msg = TextMessage(text=_CLOSED_MSG)
                else:
                    has_any_open = search_random_nearby_store(lat, lng, open_pool, seen=set(), primary_radius_km=extended_km, extended_radius_km=extended_km) is not None
                    if has_any_open:
                        reply_msg = TextMessage(text="這個時段附近有開的店都抽完了，換個時間再來試試！")
                    else:
                        reply_msg = TextMessage(text=_CLOSED_MSG)
    else:
        result = search_random_nearby_store(lat, lng, open_pool, seen=set(), primary_radius_km=extended_km, extended_radius_km=extended_km)
        if result is None:
            reply_msg = TextMessage(text=_CLOSED_MSG)
    if result:
        _add_to_seen(user_id, result["store_name"])
        _save_last_location(user_id, lat, lng)
        reply_msg = _build_random_flex(result)
    elif reply_msg is None:
        reply_msg = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
    return reply_msg


def _build_random_flex(result: dict) -> FlexMessage:
    """組裝隨機驚喜的 Flex Message。"""
    name = result["store_name"]
    dist = result["distance_km"]
    loc = _random_pool.get(name, {}).get("location", {})
    maps_url = f"https://maps.google.com/?q={loc['lat']},{loc['lng']}"
    far_phrase = _persona.get_random_far_phrase(dist)
    tagline = _random_pool.get(name, {}).get("random_tagline", "") if not far_phrase else ""
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

    must_eat_count = _get_must_eat_count(name)
    display_note = _store_notes.get(name, {}).get("display_note", "")
    contents += [
        FlexText(text=name, weight="bold", size="md", margin="md", wrap=True),
    ]
    if must_eat_count > 0:
        contents.append(FlexText(text=f"{must_eat_count} 位同好推薦 🔥", size="sm", color="#B85A2B", weight="bold"))
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
    ]
    if RATINGS_LIFF_URL:
        from urllib.parse import quote
        ratings_url = f"{RATINGS_LIFF_URL}?store={quote(name)}"
        contents.append(FlexButton(
            action=URIAction(label="查看評價 💬", uri=ratings_url),
            style="secondary",
            margin="sm",
            height="sm",
        ))
    if SHARE_LIFF_URL:
        from urllib.parse import quote
        share_url = f"{SHARE_LIFF_URL}?store={quote(name)}&lat={loc.get('lat', '')}&lng={loc.get('lng', '')}"
        if phrase:
            share_url += f"&tagline={quote(phrase)}"
        contents.append(FlexButton(
            action=URIAction(label="分享這家店 📤", uri=share_url),
            style="secondary",
            margin="sm",
            height="sm",
        ))
    contents += [
        FlexSeparator(margin="md"),
        FlexText(text="⏰ 出發前請參考各家營業時間",
                 size="xs", color="#888888", wrap=True, margin="md"),
    ]

    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    qr = QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="下一抽 🎲", text="下一抽 🎲")),
    ])
    return FlexMessage(alt_text="大叔今天幫你決定！", contents=bubble, quick_reply=qr)


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
    """依口味偏好比對 store_notes 和 hidden_gems 店家，回傳分數最高、距離最近的 2–3 家。"""
    from src.nearby_search.searcher import haversine_km
    candidates = []
    all_stores = list(_store_notes.items()) + [(name, info) for name, info in _hidden_gems.items() if info.get("visual_profile")]
    for name, info in all_stores:
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


_TASTE_INTRO_FAT   = {"fat_heavy": "肉質偏肥", "lean_heavy": "肉質偏瘦"}
_TASTE_INTRO_SKIN  = {"with_skin": "黏黏帶膠質", "no_skin": "不黏偏乾爽"}
_TASTE_INTRO_SAUCE = {"稠": "滷汁濃稠", "水": "滷汁清爽不稠"}
_TASTE_INTRO_TASTE = {"偏甜": "口味偏甜", "偏鹹": "口味偏鹹"}


def _static_taste_intros(stores: list) -> dict:
    """用 visual_profile 靜態拼出店家特色描述，不呼叫 API。回傳 {store_name: intro}。"""
    intros = {}
    for s in stores:
        name = s["store_name"]
        info = s["info"]
        vp = info.get("visual_profile", {})
        traits = []
        if vp.get("fat_ratio") in _TASTE_INTRO_FAT:
            traits.append(_TASTE_INTRO_FAT[vp["fat_ratio"]])
        if vp.get("skin") in _TASTE_INTRO_SKIN:
            traits.append(_TASTE_INTRO_SKIN[vp["skin"]])
        sc = info.get("sauce_consistency")
        if sc in _TASTE_INTRO_SAUCE:
            traits.append(_TASTE_INTRO_SAUCE[sc])
        if vp.get("sauce_taste") in _TASTE_INTRO_TASTE:
            traits.append(_TASTE_INTRO_TASTE[vp["sauce_taste"]])
        intros[name] = "、".join(traits) if traits else ""
    return intros


def _generate_taste_intros(stores: list) -> dict:
    """呼叫 Claude Haiku 為每家推薦店生成大叔風格介紹（30 字以內）。回傳 {store_name: intro}。"""
    import random as _random
    _FAT_LABEL = _TASTE_INTRO_FAT
    _SKIN_LABEL = _TASTE_INTRO_SKIN
    _SAUCE_LABEL = _TASTE_INTRO_SAUCE
    _TASTE_LABEL = _TASTE_INTRO_TASTE

    store_inputs = []
    for s in stores:
        name = s["store_name"]
        info = s["info"]
        notes = info.get("notes", "")
        toppings = info.get("available_toppings", [])
        topping_str = f"，可加點：{'、'.join(toppings)}" if toppings else ""
        if notes:
            store_inputs.append(f"【{name}】{notes[:150]}{topping_str}")
        else:
            vp = info.get("visual_profile", {})
            traits = []
            if vp.get("fat_ratio") in _FAT_LABEL:
                traits.append(_FAT_LABEL[vp["fat_ratio"]])
            if vp.get("skin") in _SKIN_LABEL:
                traits.append(_SKIN_LABEL[vp["skin"]])
            sc = info.get("sauce_consistency")
            if sc in _SAUCE_LABEL:
                traits.append(_SAUCE_LABEL[sc])
            if vp.get("sauce_taste") in _TASTE_LABEL:
                traits.append(_TASTE_LABEL[vp["sauce_taste"]])
            trait_str = "，".join(traits) if traits else "口味資料有限"
            store_inputs.append(f"【{name}】特色：{trait_str}{topping_str}")

    combined = "\n\n".join(store_inputs)
    opening_phrase = _random.choice(["哎唷", "齁", "不錯哦", "夭壽喔", "哇賽", "嘖嘖嘖"])
    system_prompt = _persona._build_system_prompt(opening_phrase)
    user_msg = (
        f"以下是幾家推薦給用戶的店家資料，請為每家店各寫一句30字以內的介紹，"
        f"只聚焦在魯肉飯的特色和好吃的地方，格式如下：\n"
        f"【店名】：介紹文\n\n"
        f"{combined}"
    )
    try:
        msg = _persona._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = msg.content[0].text.strip()
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
    tagline_text, tagline_img = get_personality_tagline(answers)
    tagline_lines = tagline_text.split("\n", 1)
    line1 = "✦ " + tagline_lines[0]
    line2 = tagline_lines[1] if len(tagline_lines) > 1 else ""
    header = FlexBox(
        layout="vertical",
        background_color="#6A3F2D",
        padding_all="lg",
        contents=[
            FlexText(text=line1, weight="bold", size="lg", color="#FFFFFF", wrap=True),
            FlexText(text=line2, size="sm", color="#FFFFFF", align="end", wrap=True, margin="sm"),
        ],
    )
    hero = FlexImage(url=tagline_img, size="full", aspect_ratio="20:13", aspect_mode="cover") if tagline_img else None
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
        hero=hero,
        header=header,
        body=FlexBox(layout="vertical", contents=body_contents, padding_all="lg"),
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#E9E1D8"),
        ),
    )
    qr_items = [
        QuickReplyItem(action=MessageAction(label="直接用 ✅", text="直接用 ✅")),
        QuickReplyItem(action=MessageAction(label="重新填 🔄", text="重新填 🔄")),
    ]
    if SHARE_TASTE_LIFF_URL:
        from urllib.parse import quote
        fat_label   = labels["fat_ratio"].get(answers.get("fat_ratio"), "都可以")
        skin_label  = labels["skin"].get(answers.get("skin"), "都可以")
        sauce_label = labels["sauce_consistency"].get(answers.get("sauce_consistency"), "都可以")
        taste_label = labels["sauce_taste"].get(answers.get("sauce_taste"), "都可以")
        share_url = (
            f"{SHARE_TASTE_LIFF_URL}"
            f"?tagline={quote(tagline_text)}"
            f"&img={quote(tagline_img or '')}"
            f"&fat={quote(fat_label)}"
            f"&skin={quote(skin_label)}"
            f"&sauce={quote(sauce_label)}"
            f"&taste={quote(taste_label)}"
        )
        qr_items.append(QuickReplyItem(action=URIAction(label="分享口味 📤", uri=share_url)))
    qr = QuickReply(items=qr_items)
    return FlexMessage(alt_text="大叔記得你的口味", contents=bubble, quick_reply=qr)


def _build_taste_flex(full: list, partial: list, intros: dict, has_more: bool = False) -> FlexMessage:
    """組裝個人化推薦的 Flex Message。full 為全符合，partial 為部分符合（score==3）。"""
    from datetime import datetime
    import zoneinfo
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei"))
    google_day = now.isoweekday() % 7
    current_hour = now.hour
    current_minute = now.minute

    header = "大叔依你的口味找到了："
    contents = [
        FlexText(text=header, weight="bold", size="md", wrap=True),
    ]
    for s in full + partial:
        name = s["store_name"]
        dist = s["distance_km"]
        is_partial = s in partial
        info = s["info"]
        loc = info.get("location", {})
        if loc:
            maps_url = f"https://maps.google.com/?q={loc['lat']},{loc['lng']}"
        else:
            maps_url = _persona.maps_url(name)
        intro = intros.get(name, "")
        must_eat_count = _get_must_eat_count(name)
        hours_entry = _store_hours.get(name)
        if hours_entry and hours_entry.get("hours"):
            periods = hours_entry["hours"].get("periods", [])
            is_open = _is_currently_open(periods, google_day, current_hour, current_minute) if periods else True
        else:
            is_open = True
        display_name = name if is_open else f"{name}（目前打烊）"
        contents.append(FlexSeparator(margin="lg"))
        contents.append(FlexText(text=display_name, weight="bold", size="md", margin="md", wrap=True, color="#333333" if is_open else "#AAAAAA"))
        if must_eat_count > 0:
            contents.append(FlexText(text=f"{must_eat_count} 位同好推薦 🔥", size="sm", color="#B85A2B", weight="bold"))
        if is_partial:
            contents.append(FlexText(text="很接近，可以考慮", size="sm", color="#B07050", wrap=True))
        if intro:
            contents.append(FlexText(text=intro, size="sm", color="#888888", wrap=True))
        contents.append(FlexText(text=f"距你約 {dist} 公里", size="sm", color="#888888"))
        contents.append(FlexButton(
            action=URIAction(label="📍 地圖", uri=maps_url),
            style="primary" if is_open else "secondary",
            margin="md",
            height="sm",
        ))
        if RATINGS_LIFF_URL:
            from urllib.parse import quote
            ratings_url = f"{RATINGS_LIFF_URL}?store={quote(name)}"
            contents.append(FlexButton(
                action=URIAction(label="查看評價 💬", uri=ratings_url),
                style="secondary",
                margin="sm",
                height="sm",
            ))
        if SHARE_LIFF_URL:
            from urllib.parse import quote
            loc = _store_notes.get(name, {}).get("location") or _hidden_gems.get(name, {}).get("location") or {}
            share_url = f"{SHARE_LIFF_URL}?store={quote(name)}&lat={loc.get('lat', '')}&lng={loc.get('lng', '')}"
            contents.append(FlexButton(
                action=URIAction(label="分享這家店 📤", uri=share_url),
                style="secondary",
                margin="sm",
                height="sm",
            ))
    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    qr_items = []
    if has_more:
        qr_items.append(QuickReplyItem(action=MessageAction(label="更多家", text="更多家")))
    qr_items.append(QuickReplyItem(action=MessageAction(label="附近巷仔口 🏘️", text="附近巷仔口店家")))
    qr = QuickReply(items=qr_items)
    return FlexMessage(alt_text="大叔幫你找到了！", contents=bubble, quick_reply=qr)


@_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    user_id = event.source.user_id

    # 打卡救援流程（優先於 NEARBY_SEARCH_ENABLED 限制）
    if CHECKIN_ENABLED and _get_checkin_rescue(user_id):
        lat = event.message.latitude
        lng = event.message.longitude
        _clear_checkin_rescue(user_id)
        nearby = _find_nearby_checkin_stores(lat, lng, radius_km=0.5)
        if nearby:
            rescue_dict = {name: db for name, db in nearby[:5]}
            _save_rescue_stores(user_id, rescue_dict)
            qr_items = [
                QuickReplyItem(action=MessageAction(
                    label=name if len(name) <= 20 else name[:19] + "…",
                    text=name,
                ))
                for name, _ in nearby[:5]
            ]
            qr_items.append(
                QuickReplyItem(action=MessageAction(label="找不到我吃的店 🤷", text="找不到我吃的店 🤷"))
            )
            rescue_msg = TextMessage(
                text="大叔幫你找到附近這幾家，選一家打卡！",
                quick_reply=QuickReply(items=qr_items),
            )
        else:
            rescue_msg = TextMessage(text="附近找不到店，這次打卡先略過")
        try:
            with ApiClient(_config) as api_client:
                messaging_api = MessagingApi(api_client)
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[rescue_msg],
                    )
                )
        except Exception:
            import traceback
            traceback.print_exc()
        return

    if not NEARBY_SEARCH_ENABLED:
        return

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
        _clear_taste_more(user_id)
        if not candidates:
            reply_msg = TextMessage(text="殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇")
        elif full:
            top_full = full[:3]
            remaining = full[3:]
            if remaining:
                _save_taste_more(user_id, remaining)
            intros = _generate_taste_intros(top_full)
            reply_msg = _build_taste_flex(top_full, [], intros, has_more=bool(remaining))
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
        reply_msg = _run_random_surprise(user_id, lat, lng)
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

    _DISTRICT_ORDER = [
        "大安區", "信義區", "中山區", "松山區", "北投區",
        "萬華區", "中正區", "大同區", "中和區", "三重區", "林口區", "泰山區",
    ]
    ordered_districts = sorted(
        district_stores.keys(),
        key=lambda d: _DISTRICT_ORDER.index(d) if d in _DISTRICT_ORDER else len(_DISTRICT_ORDER),
    )

    rows = []
    for district in ordered_districts:
        names = district_stores[district]
        if STORE_LIST_STYLE == "michelin":
            rows.append(FlexBox(
                layout="horizontal",
                contents=[
                    FlexText(text="✦", size="xs", color="#C8A86B", flex=0),
                    FlexText(text=f"  {district}", size="xs", color="#C8A86B", weight="bold", flex=1),
                ],
                margin="lg",
            ))
            rows.append(FlexSeparator(color="#3A3020", margin="sm"))
        else:
            rows.append(FlexText(text=district, size="xs", color="#aaaaaa", weight="bold", margin="md"))

        for name in names:
            loc = _store_notes[name].get("location", {})
            lat = loc.get("lat")
            lng = loc.get("lng")
            map_uri = f"https://maps.google.com/?q={lat},{lng}" if lat and lng else f"https://maps.google.com/?q={name}"
            display_name = re.sub(r'[（(].+?[）)]$', '', name)
            must_eat_count = _get_must_eat_count(name)
            if STORE_LIST_STYLE == "michelin":
                store_row_contents = [
                    FlexBox(
                        layout="horizontal",
                        contents=[
                            FlexText(text=display_name, flex=1, size="md", weight="bold", wrap=True, gravity="center", color="#F5ECD7"),
                            FlexButton(
                                action=URIAction(label="📍", uri=map_uri),
                                flex=0, height="sm", style="link", color="#C8A86B",
                            ),
                        ],
                        spacing="sm", margin="sm",
                    )
                ]
                if must_eat_count > 0:
                    store_row_contents.append(FlexText(text=f"  {must_eat_count} 位同好推薦 🔥", size="xs", color="#E8854A", margin="xs"))
                store_row_contents.append(FlexSeparator(color="#3A3020", margin="sm"))
            else:
                store_row_contents = [
                    FlexBox(
                        layout="horizontal",
                        contents=[
                            FlexText(text=display_name, flex=1, size="md", weight="bold", wrap=True, gravity="center"),
                            FlexButton(
                                action=URIAction(label="📍", uri=map_uri),
                                flex=0, height="sm", style="link",
                            ),
                        ],
                        spacing="sm",
                    )
                ]
                if must_eat_count > 0:
                    store_row_contents.append(FlexText(text=f"{must_eat_count} 位同好推薦 🔥", size="sm", color="#B85A2B", weight="bold"))
            rows.append(FlexBox(layout="vertical", contents=store_row_contents, spacing="xs"))

    if STORE_LIST_STYLE == "michelin":
        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                background_color="#1C1A14",
                padding_all="lg",
                contents=[
                    FlexText(text=f"目前可用AI辨識以下大台北 {n} 家店的魯肉飯，準確率仍在優化中\n（魯肉飯真的都長太像了 XD）\n但已經可以玩玩看！", wrap=True, size="sm", color="#C8A86B"),
                ],
            ),
            body=FlexBox(
                layout="vertical",
                contents=rows,
                spacing="xs",
                padding_all="lg",
                background_color="#252015",
            ),
            footer=FlexBox(
                layout="vertical",
                background_color="#1C1A14",
                padding_all="md",
                contents=[
                    FlexText(
                        text="持續擴充中… 🍚\n\n💡 即使丟的店家不在收錄名單中，大叔仍會分析這碗魯肉飯/滷肉飯的風格，並從現有店家中找出相似風格的供參考。",
                        wrap=True, size="xs", color="#8B7D5E",
                    ),
                ],
            ),
            styles=FlexBubbleStyles(body=FlexBlockStyle(background_color="#252015")),
        )
    else:
        header_text = f"目前可用AI辨識以下大台北 {n} 家店的魯肉飯，準確率仍在優化中\n（魯肉飯真的都長太像了 XD）\n但已經可以玩玩看！"
        footer_text = "持續擴充中… 🍚\n\n💡 即使丟的店家不在收錄名單中，大叔仍會分析這碗魯肉飯/滷肉飯的風格，並從現有店家中找出相似風格的供參考。"
        bubble = FlexBubble(
            header=FlexBox(
                layout="vertical",
                contents=[FlexText(text=header_text, wrap=True, size="sm", color="#555555")],
                padding_all="lg",
            ),
            body=FlexBox(layout="vertical", contents=rows, spacing="sm", padding_all="lg"),
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
            checkin = d.get("checkin_confirmed", 0)
            rating = d.get("rating_submitted", 0)
            return (
                f"  丟照片：{img} 次\n  附近相似風格：{near} 次\n"
                f"  隨機驚喜：{rand} 次\n  個人化：{personal} 次\n"
                f"  就是這家：{checkin} 次\n  回答評價：{rating} 次"
            )

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
            must_eat_count = _get_must_eat_count(name)
            if i > 0:
                rows.append(FlexSeparator(margin="sm", color="#E6D9C8"))
            store_row_contents = [
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
            ]
            if must_eat_count > 0:
                store_row_contents.append(FlexText(text=f"{must_eat_count} 位同好推薦 🔥", size="sm", color="#B85A2B", weight="bold"))
            rows.append(FlexBox(layout="vertical", contents=store_row_contents, spacing="xs"))

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
        must_eat_count = _get_must_eat_count(name)
        if i > 0:
            rows.append(FlexSeparator(margin="md", color="#E6D9C8"))
        store_row_contents = [
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
        ]
        if must_eat_count > 0:
            store_row_contents.append(FlexText(text=f"{must_eat_count} 位同好推薦 🔥", size="sm", color="#B85A2B", weight="bold"))
        rows.append(FlexBox(layout="vertical", contents=store_row_contents, spacing="xs"))

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
        must_eat_count = _get_must_eat_count(name)
        contents.append(FlexSeparator(margin="lg"))
        display_name = name if is_open else f"{name}（目前打烊）"
        contents.append(FlexText(text=display_name, weight="bold", size="md", margin="md", wrap=True, color="#333333" if is_open else "#AAAAAA"))
        if must_eat_count > 0:
            contents.append(FlexText(text=f"{must_eat_count} 位同好推薦 🔥", size="sm", color="#B85A2B", weight="bold"))
        contents.append(FlexText(text=f"距你約 {dist} 公里", size="sm", color="#888888"))
        contents.append(FlexButton(
            action=URIAction(label="📍 地圖", uri=maps_url),
            style="primary" if is_open else "secondary",
            margin="md",
            height="sm",
        ))
        if RATINGS_LIFF_URL:
            from urllib.parse import quote
            ratings_url = f"{RATINGS_LIFF_URL}?store={quote(name)}"
            contents.append(FlexButton(
                action=URIAction(label="查看評價 💬", uri=ratings_url),
                style="secondary",
                margin="sm",
                height="sm",
            ))
        if SHARE_LIFF_URL:
            from urllib.parse import quote
            share_url = f"{SHARE_LIFF_URL}?store={quote(name)}&lat={lat or ''}&lng={lng or ''}"
            contents.append(FlexButton(
                action=URIAction(label="分享這家店 📤", uri=share_url),
                style="secondary",
                margin="sm",
                height="sm",
            ))
    bubble = FlexBubble(
        body=FlexBox(layout="vertical", contents=contents, padding_all="lg")
    )
    return FlexMessage(alt_text="附近巷仔口店家", contents=bubble)


def _find_nearby_checkin_stores(lat: float, lng: float, radius_km: float = 0.5) -> list:
    """搜尋兩個資料庫 radius_km 內的店家，回傳 [(store_name, db_source), ...]，依距離排序。"""
    from src.nearby_search.searcher import haversine_km
    result = []
    for name, data in _store_notes.items():
        loc = data.get("location")
        if not loc:
            continue
        dist = haversine_km(lat, lng, loc["lat"], loc["lng"])
        if dist <= radius_km:
            result.append((name, "store_notes", dist))
    for name, data in _hidden_gems.items():
        if name in _HIDDEN_GEMS_RANDOM_EXCLUDE:
            continue
        loc = data.get("location")
        if not loc:
            continue
        dist = haversine_km(lat, lng, loc["lat"], loc["lng"])
        if dist <= radius_km:
            result.append((name, "hidden_gems", dist))
    result.sort(key=lambda x: x[2])
    seen = set()
    deduped = []
    for name, db, dist in result:
        if name not in seen:
            seen.add(name)
            deduped.append((name, db, dist))
    return [(name, db) for name, db, _ in deduped]


def _build_footprint_flex(user_id: str):
    """讀取用戶打卡記錄，組裝足跡 Flex Message。若無記錄回傳 None；Firestore 無法連線回傳 TextMessage。"""
    if _db is None:
        return TextMessage(text="目前無法讀取足跡，請稍後再試。")
    try:
        import zoneinfo
        from urllib.parse import quote
        user_doc = _db.collection("user_footprint").document(user_id).get()
        records_ref = (
            _db.collection("user_footprint")
            .document(user_id)
            .collection("records")
        )
        docs = list(records_ref.order_by("checked_in_at", direction="DESCENDING").stream())
    except Exception:
        return TextMessage(text="目前無法讀取足跡，請稍後再試。")

    if not docs:
        return None

    visits = [doc.to_dict() for doc in docs]

    # 去重，依最新造訪順序排列
    seen_set: set = set()
    unique_stores: list = []
    for v in visits:
        name = v.get("store_name", "")
        if name and name not in seen_set:
            seen_set.add(name)
            unique_stores.append(name)

    unique_count = len(unique_stores)
    total_stores = 112

    # 稱號資料
    user_data = user_doc.to_dict() if user_doc.exists else {}
    current_title = user_data.get("current_title") or _get_title(unique_count)
    title_number = user_data.get("title_number") or user_id[-4:]
    title_display = f"{current_title}#{title_number}"
    favorites = set(user_data.get("favorites", []))

    # 最近一次打卡
    recent_name = visits[0].get("store_name", "")
    recent_ts = visits[0].get("checked_in_at")
    if recent_ts and hasattr(recent_ts, "astimezone"):
        recent_date = recent_ts.astimezone(zoneinfo.ZoneInfo("Asia/Taipei")).strftime("%m/%d")
    else:
        recent_date = ""

    display_stores = unique_stores[:10]

    certification = _TITLE_CERTIFICATIONS.get(current_title, "")
    next_info = ""
    for next_title, threshold in _TITLE_NEXT:
        if unique_count < threshold:
            next_info = f"再吃 {threshold - unique_count} 家升級{next_title}！"
            break

    header_contents = [
        FlexText(text="🍚 魯肉飯足跡", weight="bold", size="md", color="#FFFFFF"),
        FlexText(
            text=f"踩點 {unique_count} / {total_stores} 家",
            size="xxl", weight="bold", color="#FFD700", margin="sm",
        ),
        FlexText(text=title_display, size="sm", color="#FFD700", margin="xs"),
    ]
    if certification:
        header_contents.append(FlexText(
            text=f"大叔認證：{certification}",
            size="xs", color="#C8A97E", wrap=True, margin="sm",
        ))

    header = FlexBox(
        layout="vertical",
        background_color="#4B2F24",
        padding_all="lg",
        contents=header_contents,
    )

    body_contents = []
    if next_info:
        body_contents.append(FlexText(
            text=next_info,
            size="sm", color="#B85A2B", wrap=True, weight="bold",
        ))
        body_contents.append(FlexSeparator(margin="md"))

    if recent_name:
        body_contents.append(FlexText(
            text=f"最近：{recent_name}" + (f"（{recent_date}）" if recent_date else ""),
            size="sm", color="#888888", wrap=True,
        ))
        body_contents.append(FlexSeparator(margin="md"))

    for i, name in enumerate(display_stores):
        heart = "❤️" if name in favorites else "🤍"
        loc = (_store_notes.get(name) or _hidden_gems.get(name) or {}).get("location", {})
        row_buttons = [
            FlexButton(action=PostbackAction(label=heart, data=f"fav:{name}"), flex=0, height="sm", style="link"),
        ]
        if RATINGS_LIFF_URL:
            row_buttons.append(FlexButton(action=URIAction(label="💬", uri=f"{RATINGS_LIFF_URL}?store={quote(name)}"), flex=0, height="sm", style="link"))
        if SHARE_LIFF_URL:
            share_url = f"{SHARE_LIFF_URL}?store={quote(name)}&lat={loc.get('lat', '')}&lng={loc.get('lng', '')}"
            row_buttons.append(FlexButton(action=URIAction(label="📤", uri=share_url), flex=0, height="sm", style="link"))
        body_contents.append(FlexBox(
            layout="horizontal",
            contents=[
                FlexText(text=f"✅  {name}", flex=1, size="sm", weight="bold", color="#4B2F24", wrap=True, gravity="center"),
                *row_buttons,
            ],
            margin="sm" if i > 0 else "md",
        ))

    remaining = unique_stores[10:]
    bubble_size = "giga" if remaining else None
    bubble = FlexBubble(
        size=bubble_size,
        header=header,
        body=FlexBox(layout="vertical", contents=body_contents, padding_all="lg"),
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#F9F5F0"),
        ),
    )

    if not remaining:
        return FlexMessage(alt_text=f"魯肉飯足跡 {unique_count}/{total_stores} 家", contents=bubble)

    # 第二張卡：剩餘店家
    more_contents = []
    for i, name in enumerate(remaining):
        heart = "❤️" if name in favorites else "🤍"
        loc = (_store_notes.get(name) or _hidden_gems.get(name) or {}).get("location", {})
        row_buttons = [
            FlexButton(action=PostbackAction(label=heart, data=f"fav:{name}"), flex=0, height="sm", style="link"),
        ]
        if RATINGS_LIFF_URL:
            row_buttons.append(FlexButton(action=URIAction(label="💬", uri=f"{RATINGS_LIFF_URL}?store={quote(name)}"), flex=0, height="sm", style="link"))
        if SHARE_LIFF_URL:
            share_url = f"{SHARE_LIFF_URL}?store={quote(name)}&lat={loc.get('lat', '')}&lng={loc.get('lng', '')}"
            row_buttons.append(FlexButton(action=URIAction(label="📤", uri=share_url), flex=0, height="sm", style="link"))
        more_contents.append(FlexBox(
            layout="horizontal",
            contents=[
                FlexText(text=f"✅  {name}", flex=1, size="sm", weight="bold", color="#4B2F24", wrap=True, gravity="center"),
                *row_buttons,
            ],
            margin="sm" if i > 0 else "none",
        ))
    more_bubble = FlexBubble(
        size="giga",
        header=FlexBox(
            layout="vertical",
            background_color="#4B2F24",
            padding_all="lg",
            contents=[
                FlexText(text="🍚 魯肉飯足跡", weight="bold", size="md", color="#FFFFFF"),
                FlexText(text=f"全部 {unique_count} 家（續）", size="sm", color="#FFD700", margin="sm"),
            ],
        ),
        body=FlexBox(layout="vertical", contents=more_contents, padding_all="lg"),
        styles=FlexBubbleStyles(
            body=FlexBlockStyle(background_color="#F9F5F0"),
        ),
    )

    return FlexMessage(
        alt_text=f"魯肉飯足跡 {unique_count}/{total_stores} 家",
        contents=FlexCarousel(contents=[bubble, more_bubble]),
    )


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

3. 🔥 同好推薦
大叔評論完之後，可以對這家店按「必吃」留下評價。你的評價會顯示在店家頁面上，讓其他同好看到這碗值不值得衝！

4. 📍 個人足跡
每打卡一家店，就會在個人足跡看到已踩點的記錄，以及距離下一個職稱還差幾家。

5. ⏳ 等待說明：
初次回應稍等幾秒暖機，之後就快了（但可能還是要幾秒～～被打）

6. 📌 大叔的承諾
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
            elif CHECKIN_ENABLED and text == "就是這家 ✅":
                pending = _get_pending_checkin(user_id)
                if pending:
                    _clear_pending_checkin(user_id)
                    if not _is_admin(user_id):
                        _track("checkin_confirmed")
                    reply = _process_checkin_with_title(user_id, pending["store"], pending["db"])
                else:
                    reply = TextMessage(text=_text_reply_greeting())
            elif CHECKIN_ENABLED and text == "找不到我吃的店 🤷":
                _clear_rescue_stores(user_id)
                reply = TextMessage(text="拍謝！這家大叔還不認識，下次再來！")
            elif CHECKIN_ENABLED and text == "打卡這碗 📍":
                _set_checkin_rescue(user_id)
                reply = TextMessage(
                    text="好！分享一下你在哪，大叔幫你找附近的店 📍",
                    quick_reply=QuickReply(items=[
                        QuickReplyItem(action=LocationAction(label="分享位置 📍"))
                    ]),
                )
            elif CHECKIN_ENABLED and text in ("必吃 👍", "普通 😐", "不能只有我吃到 🤫"):
                pending_store = _get_pending_rating(user_id)
                if pending_store:
                    _clear_pending_rating(user_id)
                    rating_map = {"必吃 👍": "must_eat", "普通 😐": "neutral", "不能只有我吃到 🤫": "bad"}
                    if not _is_admin(user_id):
                        _track("rating_submitted", f"rating_{rating_map[text]}")
                    _save_rating_record(user_id, pending_store, rating_map[text])
                    nearby_qr_items = [QuickReplyItem(action=LocationAction(label="找附近類似的 📍"))] if NEARBY_SEARCH_ENABLED else []
                    if nearby_qr_items:
                        reply = TextMessage(text="感謝評價！", quick_reply=QuickReply(items=nearby_qr_items))
                    else:
                        reply = TextMessage(text="感謝評價！")
                else:
                    reply = TextMessage(text=_text_reply_greeting())
            elif CHECKIN_ENABLED and text == "我的稱號":
                if _db is None:
                    reply = TextMessage(text="目前無法讀取稱號，請稍後再試。")
                else:
                    try:
                        user_doc = _db.collection("user_footprint").document(user_id).get()
                        records_ref = _db.collection("user_footprint").document(user_id).collection("records")
                        docs = list(records_ref.stream())
                        if not docs:
                            title_num = user_id[-4:]
                            display = f"無職轉生者#{title_num}"
                            reply = _build_title_flex(display, "無職轉生者", 0)
                        else:
                            unique_stores = {d.to_dict().get("store_name") for d in docs}
                            unique_count = len(unique_stores)
                            user_data = user_doc.to_dict() if user_doc.exists else {}
                            current_title = user_data.get("current_title") or _get_title(unique_count)
                            title_number = user_data.get("title_number") or user_id[-4:]
                            display = f"{current_title}#{title_number}"
                            reply = _build_title_flex(display, current_title, unique_count)
                    except Exception:
                        reply = TextMessage(text="目前無法讀取稱號，請稍後再試。")
            elif CHECKIN_ENABLED and text == "足跡":
                flex = _build_footprint_flex(user_id)
                if flex is None:
                    reply = TextMessage(
                        text="還沒有打卡記錄！下次吃魯肉飯，傳張照片給大叔，就能開始累積足跡 🍚",
                    )
                else:
                    reply = flex
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
            elif text == "更多家":
                more = _get_taste_more(user_id)
                if more:
                    next_batch = more[:3]
                    remaining = more[3:]
                    if remaining:
                        _save_taste_more(user_id, remaining)
                    else:
                        _clear_taste_more(user_id)
                    intros = _static_taste_intros(next_batch)
                    reply = _build_taste_flex(next_batch, [], intros, has_more=bool(remaining))
                else:
                    reply = TextMessage(text="已經沒有更多符合的店囉！")
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
            elif text == "下一抽 🎲":
                last_loc = _get_last_location(user_id)
                if last_loc:
                    reply = _run_random_surprise(user_id, last_loc["lat"], last_loc["lng"])
                else:
                    reply = TextMessage(
                        text="大叔忘了你在哪了！分享位置讓大叔再幫你抽一次 🎲",
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(action=LocationAction(label="分享位置 📍"))
                        ]),
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
                rescue_stores = _get_rescue_stores(user_id) if CHECKIN_ENABLED else None
                if rescue_stores and text in rescue_stores:
                    db_source = rescue_stores[text]
                    _clear_rescue_stores(user_id)
                    if NEARBY_SEARCH_ENABLED:
                        _save_session(user_id, text)
                    reply = _process_checkin_with_title(user_id, text, db_source)
                else:
                    reply = TextMessage(text=_text_reply_greeting())
            if reply is not None:
                send_msgs = reply if isinstance(reply, list) else [reply]
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=send_msgs,
                    )
                )
    except Exception:
        import traceback
        traceback.print_exc()


@_handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件（目前用於愛店 toggle）。"""
    try:
        user_id = event.source.user_id
        data = event.postback.data
        if data.startswith("fav:") and _db is not None:
            store_name = data[4:]
            user_ref = _db.collection("user_footprint").document(user_id)
            user_doc = user_ref.get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            favorites = user_data.get("favorites", [])
            if store_name in favorites:
                favorites.remove(store_name)
            else:
                favorites.append(store_name)
            user_ref.set({"favorites": favorites}, merge=True)
            # 回傳更新後的足跡卡
            with ApiClient(_config) as api_client:
                messaging_api = MessagingApi(api_client)
                flex = _build_footprint_flex(user_id)
                if flex:
                    messaging_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[flex],
                        )
                    )
    except Exception:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
