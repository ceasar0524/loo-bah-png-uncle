## 1. 稱號計算邏輯

- [x] 1.1 實作 `_get_title(unique_count)` 函式，依稱號門檻（0-4 無職轉生者、5-14 肉汁騎士、15-29 滷鍋守護者、30-59 魯肉飯勇者、60+ 魯肉飯大神）回傳稱號（Title calculation based on check-in count）
- [x] 1.2 實作 `_get_title_number(user_id, title)` 函式，依代號產生方式：無職轉生者用 user_id 後4碼，其餘使用 Firestore transaction 遞增 `title_counter/<title>`（Title number assignment）
- [x] 1.3 確認 Firestore 資料結構：`user_footprint/<user_id>` 新增 `current_title`、`title_number` 欄位，`title_counter/<title>` 作為全域計數器

## 2. 升級事件偵測與儀式感訊息

- [x] 2.1 打卡完成後重新計算稱號，偵測升級事件：比對新稱號與 Firestore `current_title`，觸發升級時更新稱號門檻對應欄位（Title calculation based on check-in count）
- [x] 2.2 升級時以大叔 persona 語氣產生儀式感訊息，作為獨立回覆送出（Upgrade ceremony message）
- [x] 2.3 確認升級儀式感訊息在打卡確認回覆之後送出（Upgrade ceremony delivered）

## 3. 代號查詢 handler（代號查詢入口）

- [x] 3.1 在 webhook handler 新增「我的代號」關鍵字處理，讀取 Firestore `current_title`、`title_number`、打卡唯一數，回覆查詢結果（Title and number query）
- [x] 3.2 用戶無打卡記錄時回覆預設無職轉生者稱號與引導訊息（User queries title with no check-ins）

## 4. 足跡 Flex Message 加入稱號

- [x] 4.1 修改 `_build_footprint_flex` 函式，在 Flex Message 頂部加入稱號與代號顯示（Footprint query）
