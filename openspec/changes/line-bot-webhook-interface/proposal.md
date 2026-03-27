## Why

辨識系統目前只能透過 CLI（`recognize.py`）使用，需要一個對外入口讓一般使用者能透過 LINE 傳照片並收到大叔回應。LINE Bot 是台灣最普及的通訊工具，門檻低、不需要額外安裝。

## What Changes

- 新增 `app.py`：Flask 應用，提供 LINE Messaging API webhook endpoint
- 接收使用者傳入的圖片訊息，下載後丟進現有 `pipeline.run()`，將回應傳回 LINE
- 新增 `LINE_CHANNEL_SECRET` 與 `LINE_CHANNEL_ACCESS_TOKEN` 環境變數需求
- 更新 `requirements.txt` 加入 `flask`、`line-bot-sdk`

## Capabilities

### New Capabilities

- `line-bot-webhook`: LINE Bot webhook 入口，接收圖片訊息並回傳大叔回應

### Modified Capabilities

(none)

## Impact

- 新增程式碼：`app.py`
- 修改：`requirements.txt`（新增 flask、line-bot-sdk）
- 新增環境變數：`LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN`
