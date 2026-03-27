## 1. 環境設定

- [x] 1.1 在 `requirements.txt` 新增 `flask` 與 `line-bot-sdk`（Environment variable configuration）
- [x] 1.2 在 `.env` 新增 `LINE_CHANNEL_SECRET` 與 `LINE_CHANNEL_ACCESS_TOKEN` 佔位欄位（Environment variable configuration）

## 2. Webhook 入口實作

- [x] 2.1 建立 `app.py`，實作 `/webhook` POST endpoint 並驗證 LINE 簽名（LINE webhook endpoint）
- [x] 2.2 實作圖片訊息處理：下載圖片 → tempfile → pipeline.run() → 回覆大叔回應（Image message handling）
- [x] 2.3 確認非圖片訊息（文字、貼圖）不回覆，靜默忽略（Non-image message handling）
- [x] 2.4 確認啟動時缺少環境變數會立即報錯（Environment variable configuration）

## 3. 本機驗證

- [x] 3.1 安裝新依賴，確認 `app.py` 可正常啟動（`python app.py`）
- [ ] 3.2 用 ngrok 暴露本機 port，填入 LINE Developers webhook URL，傳照片測試完整流程（需先建立 LINE Bot channel）
