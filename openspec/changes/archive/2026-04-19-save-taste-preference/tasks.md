## 1. Firestore 讀寫

- [x] 1.1 實作 `_save_taste_preference(user_id, answers)` 非同步寫入 Firestore `user_preferences` collection，包含 `taste` 欄位與 `updated_at` timestamp（save taste preferences to Firestore）
- [x] 1.2 實作 `_load_taste_preference(user_id)` 讀取 Firestore `user_preferences/<user_id>`，回傳 answers dict 或 None（load saved taste preferences）

## 2. Session 狀態擴充

- [x] 2.1 新增 `_save_taste_save_pending(user_id, answers)`、`_get_taste_save_pending(user_id)`、`_clear_taste_save_pending(user_id)` 輔助函式（Firestore 儲存結構）
- [x] 2.2 新增 `_save_taste_loaded(user_id, answers)`、`_get_taste_loaded(user_id)`、`_clear_taste_loaded(user_id)` 輔助函式（Session 狀態擴充）

## 3. 問卷完成後詢問儲存

- [x] 3.1 修改 `handle_text` 中四題答完的邏輯：依儲存詢問時機設計，將答案存入 `taste_save_pending`，回覆「要儲存你的偏好嗎？」並附 Quick Reply「儲存 ✅」/「不用 ❌」，不再直接設定 `__taste__` session（handle taste quiz Quick Reply responses）
- [x] 3.2 在 `handle_text` 攔截「儲存 ✅」/「不用 ❌」回覆（當 `taste_save_pending` 存在時），執行對應的儲存或跳過，清除 `taste_save_pending`，設定 `__taste__` session，詢問位置（handle preference save confirmation）

## 4. 已有偏好的快速套用流程

- [x] 4.1 修改「個人化」觸發邏輯（已有偏好的觸發流程）：先呼叫 `_load_taste_preference`，若有偏好則顯示摘要並回覆 Quick Reply「直接用 ✅」/「重新填 🔄」，將偏好存入 `taste_loaded`（load saved taste preferences）
- [x] 4.2 在 `handle_text` 攔截新關鍵字「直接用 ✅」/「重新填 🔄」回覆（當 `taste_loaded` 存在時），分別處理 apply saved preferences directly 或清除後重新開始問卷（handle 直接用 and 重新填 Quick Reply responses；overwrite saved preferences）
