import os
import tempfile
import threading

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import ImageMessageContent, MessageEvent

from src import clip_model
from src.pipeline import run as pipeline_run

# 啟動時預載 CLIP 模型，避免第一個請求才觸發載入
clip_model.get_model()

app = Flask(__name__)

# 啟動時讀取，缺少則立即 KeyError 報錯
_LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
_LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

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


def _process_image(reply_token, message_id):
    with ApiClient(_config) as api_client:
        blob_api = MessagingApiBlob(api_client)
        image_bytes = blob_api.get_message_content(message_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        reply_text = pipeline_run(tmp_path, index_path="index.npz")
    except Exception:
        import traceback
        traceback.print_exc()
        reply_text = "大叔出去買魯肉飯，等一下！再試一次啦！"
    finally:
        os.unlink(tmp_path)

    try:
        with ApiClient(_config) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
    except Exception:
        import traceback
        traceback.print_exc()


@_handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    threading.Thread(
        target=_process_image,
        args=(event.reply_token, event.message.id),
        daemon=True,
    ).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
