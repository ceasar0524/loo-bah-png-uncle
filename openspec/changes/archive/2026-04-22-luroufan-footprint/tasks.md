## 1. Firestore 打卡記錄儲存

- [x] 1.1 實作 `_save_checkin_record(user_id, store_name, db_source)` 函式，依照 Firestore 資料結構（`user_footprint/<user_id>/records/<auto_id>`）非同步寫入（Firestore check-in storage）
- [x] 1.2 確認寫入非同步執行於 background thread，不阻塞 webhook 回應

## 2. 照片辨識回應加入打卡入口（Photo recognition response includes check-in entry point）

- [x] 2.1 實作 Photo recognition response includes check-in entry point：辨識高信心度成功時（Check-in after successful photo recognition），將店名存入 session `pending_checkin`，在 Quick Reply 加入「就是這家 ✅」
- [x] 2.2 辨識失敗/平手的補救路徑：辨識平手或失敗時（Check-in rescue via location when recognition fails），在 Quick Reply 加入「打卡這碗 📍」

## 3. 打卡確認 handler

- [x] 3.1 打卡確認流程：在 webhook handler 新增「就是這家 ✅」訊息處理（Check-in confirmation handler），從 session 讀取 `pending_checkin`，呼叫 `_save_checkin_record`，清除 session，回覆確認訊息

## 4. 打卡救援流程（Check-in rescue handler）

- [x] 4.1 在 webhook handler 新增「打卡這碗 📍」訊息處理（Check-in rescue handler）：設定 session `checkin_rescue: True`，回覆 LocationAction Quick Reply
- [x] 4.2 location event handler 中，偵測 `checkin_rescue` session flag，搜尋兩個資料庫 500 公尺內店家，以 Quick Reply 列出（最多 5 家）（Location received during check-in rescue）
- [x] 4.3 用戶點選店名後記錄打卡、清除 `checkin_rescue` session（Nearby stores found）
- [x] 4.4 附近無店時回覆提示訊息（No nearby stores found）

## 5. 足跡查詢顯示（Footprint query）

- [x] 5.1 實作 `_build_footprint_flex(user_id)` 函式（Footprint query）：讀取 Firestore 記錄，去重計算唯一店家數，依足跡查詢顯示規格組裝 Flex Message（Footprint keyword handler）
- [x] 5.2 在 webhook handler 新增「足跡」關鍵字處理，呼叫 `_build_footprint_flex` 回覆
- [x] 5.3 用戶無打卡記錄時回覆引導訊息（User queries footprint with no records）
