## 1. 資料準備

- [x] 1.1 在 store_notes.json 各店家新增 `location` 欄位（Store location data）：填入 22 家店的經緯度（lat、lng）

## 2. 附近搜尋模組

- [x] 2.1 建立 `src/nearby_search/` 模組
- [x] 2.2 實作 Haversine 距離計算函式（距離計算用 Haversine 公式）
- [x] 2.3 實作 `search_nearby_stores(matched_store, user_lat, user_lng, store_notes, radius_km=3, top_n=3)` — 用 visual_profile 比對做風格搜尋、依相似度排序、距離篩選、排除原始辨識店家（Search nearby stores by profile similarity）
- [x] 2.4 實作 visual_profile 相似度計算函式（比對 fat_ratio、skin、sauce_color、rice_quality 四個欄位，回傳 0~1 分數）

## 3. Session 管理

- [x] 3.1 在 `app.py` 新增 in-memory session dict `{user_id: (query_vector, timestamp)}`（Session 狀態用 in-memory dict 暫存查詢向量）
- [x] 3.2 實作 session TTL 清除機制（5 分鐘過期）

## 4. LINE Bot Webhook 擴充

- [x] 4.0 在 `app.py` 新增 `NEARBY_SEARCH_ENABLED` 環境變數開關（預設 `true`），功能異常時可在 Cloud Run 設為 `false` 快速關閉
- [x] 4.1 辨識成功後在回應附加「找附近類似的 📍」Quick Reply 按鈕（Quick Reply button after recognition response；Quick Reply 按鈕只在辨識成功時顯示，且須檢查 `NEARBY_SEARCH_ENABLED`）
- [x] 4.2 處理 Quick Reply 按鈕點擊事件，回覆請用戶分享位置的訊息（使用 LocationAction 直接開啟位置選擇器，無需額外 postback 步驟）
- [x] 4.3 處理 LINE location message 事件（Handle location message）：取出 session 向量、呼叫附近搜尋、回傳大叔推薦回應
- [x] 4.4 處理 session 過期情況：無 session 時提示用戶重新傳照片（Location received with expired session）

## 5. 大叔回應擴充

- [x] 5.1 在 `persona.py` 新增 `generate_nearby` 方法，接受推薦店家清單，生成 in-character 附近推薦回應（Nearby recommendation response），每家附 Google Maps 靜態連結（`https://maps.google.com/?q=<lat>,<lng>`）
- [x] 5.2 新增無附近結果時的 in-character 回應（No nearby stores found）

## 6. 測試與驗證

- [x] 6.1 本機測試 Haversine 距離計算正確性
- [x] 6.2 本機測試 Quick Reply 按鈕顯示與位置請求流程
- [x] 6.3 本機測試附近搜尋結果排序與距離篩選
- [x] 6.4 部署到 Cloud Run 並進行端到端測試
