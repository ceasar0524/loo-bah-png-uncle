## Context

現有辨識系統已有完整的 pipeline（`src/pipeline.py`），只需要一個薄薄的 web 層接收 LINE 傳來的圖片並呼叫 pipeline。LINE Messaging API 使用 webhook 模式：使用者傳訊息 → LINE 伺服器 POST 到我們的 endpoint → 我們呼叫 Reply Message API 回覆。

## Goals / Non-Goals

**Goals:**

- 提供 `/webhook` POST endpoint 接收 LINE 事件
- 收到圖片訊息時，下載圖片、呼叫 pipeline、回覆大叔回應
- 驗證 LINE 簽名（防止偽造請求）
- 收到非圖片訊息時靜默忽略

**Non-Goals:**

- 支援群組聊天或多人互動
- 儲存使用者上傳的照片
- 提供管理介面或統計資訊

## Decisions

**使用 Flask + line-bot-sdk v3。** Flask 輕量，line-bot-sdk v3 是目前官方維護的版本，有型別標注且 API 乾淨。

**圖片用暫存檔傳給 pipeline。** pipeline.run() 接受檔案路徑，LINE 下載的 bytes 先寫入 tempfile，用完即刪。

**環境變數在啟動時讀取，若缺少則啟動失敗。** `LINE_CHANNEL_SECRET` 和 `LINE_CHANNEL_ACCESS_TOKEN` 直接用 `os.environ[]`（非 `.get()`），確保遺漏時立即報錯而非在第一次請求時才崩潰。

## Risks / Trade-offs

- LINE Reply Token 有效期限約 1 分鐘。若 pipeline 處理時間超過（例如 CLIP 模型 cold start），回覆會失敗。Cloud Run 預先載入模型可緩解，本機測試不受影響。
- 非圖片訊息（文字、貼圖）靜默忽略，使用者不會收到任何回覆，這是預期行為。
