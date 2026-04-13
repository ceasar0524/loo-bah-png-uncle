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
    QuickReply,
    QuickReplyItem,
)
from linebot.v3.messaging import (
    FlexMessage,
    FlexBubble,
    FlexBox,
    FlexButton,
    FlexText,
    URIAction,
)
from linebot.v3.webhooks import ImageMessageContent, LocationMessageContent, MessageEvent, TextMessageContent

from src import clip_model
from src.nearby_search import search_nearby_stores
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
# 格式：{user_id: (matched_store, timestamp)}
_SESSION_TTL = 300  # 5 分鐘
_sessions: dict = {}
_sessions_lock = threading.Lock()


def _cleanup_sessions() -> None:
    """移除超過 TTL 的 session（在 lock 內呼叫）。"""
    now = time.time()
    expired = [uid for uid, (_, ts) in _sessions.items() if now - ts > _SESSION_TTL]
    for uid in expired:
        del _sessions[uid]


def _save_session(user_id: str, matched_store: str) -> None:
    with _sessions_lock:
        _cleanup_sessions()
        _sessions[user_id] = (matched_store, time.time())


def _get_session(user_id: str):
    """回傳 matched_store，若無 session 或已過期則回傳 None。"""
    with _sessions_lock:
        entry = _sessions.get(user_id)
        if entry is None:
            return None
        matched_store, ts = entry
        if time.time() - ts > _SESSION_TTL:
            del _sessions[user_id]
            return None
        return matched_store


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


@_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    if not NEARBY_SEARCH_ENABLED:
        return

    user_id = event.source.user_id
    matched_store = _get_session(user_id)

    if not matched_store:
        reply_text = "傳張照片給大叔看，大叔才知道你在找什麼路線！"
    else:
        if not _is_admin(user_id):
            logging.info("[event] nearby_search_triggered")
        lat = event.message.latitude
        lng = event.message.longitude
        results, any_in_radius = search_nearby_stores(matched_store, lat, lng, _store_notes)
        results_for_persona = sorted(results[:2], key=lambda x: x["distance_km"])
        reply_text = _persona.generate_nearby(matched_store, results_for_persona, any_in_radius)

    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
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
                        FlexText(text=display_name, flex=1, size="sm", wrap=True, gravity="center"),
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

    header_text = f"目前收錄 {n} 家店，準確率仍在優化中\n（魯肉飯真的都長太像了 XD）\n但已經可以玩玩看！"
    footer_text = "持續擴充中… 🍚\n\n💡 即使丟的店家不在收錄名單中，大叔仍會分析這碗魯肉飯/滷肉飯的風格，並從現有店家中找出相似風格的供參考。\n\n注意事項：\n⚠️ 此工具為實驗性質，評論僅供參考\n每個人口味不同，最重要的是找到屬於自己心中最愛的魯肉飯 🍚"

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


_HOW_TO_USE_TEXT = """怎麼用：
1. 丟一張魯肉飯照片
📸 小提示：直接拍攝魯肉飯效果最佳，截圖或網路圖片辨識較不準。

2. 看大叔怎麼說
🧑‍🍳 小提示：大叔只看得懂魯肉飯，恕不陪聊😆（陪聊要算鐘點費XD

3. ⏳ 等待說明：
初次回應稍等幾秒暖機，之後就快了（但可能還是要幾秒～～被打）

4. 📌 大叔的承諾
大叔很健忘，看完就忘，照片不留存，放心傳、安心吃。

📩 有問題或回饋歡迎寫信🙏（大叔玻璃心，鞭小力）：ceasar0524@gmail.com"""


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


@_handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    text = event.message.text.strip() if event.message.text else ""
    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            if text == "怎麼用":
                reply = TextMessage(text=_HOW_TO_USE_TEXT)
            elif text == "店家清單":
                reply = _build_store_list_flex()
            else:
                reply = TextMessage(text=_text_reply_greeting())
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
