## 1. Session 與觸發邏輯

- [x] 1.1 新增 `_save_taste_quiz` 和 `_get_taste_quiz` 輔助函式，將 `taste_quiz` 存為 `_sessions[user_id]` 的獨立 key（session 狀態管理），不修改現有 session 函式
- [x] 1.2 在 `handle_text` 新增「個人化」觸發方式，實作以四題 Quick Reply 依序收集口味偏好的起始邏輯，觸發 taste preference quiz flow，設定 taste quiz session 狀態並回覆第一題（non-image message handling）
- [x] 1.3 在 `handle_text` 關鍵字判斷中加入問卷答案選項（偏肥、偏瘦、黏黏、不黏、稠、不稠、偏甜、偏鹹、都可以），handle taste quiz Quick Reply responses，儲存答案、推進到下一題
- [x] 1.4 四題答完後設定 session store 為 `__taste__`，提示用戶分享位置（handle location message with taste session 的前置條件）

## 2. 比對與推薦邏輯

- [x] 2.1 實作 taste-based store matching 比對邏輯：加權計分，對 `store_notes` 每家店計算 match score（0–4 分），建立欄位對應（`visual_profile.fat_ratio`、`visual_profile.skin`、頂層 `sauce_consistency`、`visual_profile.sauce_taste`）
- [x] 2.2 結合位置，篩選 10 km 內的店家，依分數排序後回傳 2–3 家；實作 taste quiz session management，同分以距離優先
- [x] 2.3 實作 fallback：no stores found within radius 時回傳提示訊息；fewer than 2 matching stores 時補足至 3 家並附說明

## 3. 回覆格式

- [x] 3.1 呼叫 Claude Haiku 根據每家店的 `notes` 和 `available_toppings` 生成大叔風格介紹（大叔風格店家介紹），一次呼叫生成所有推薦店家
- [x] 3.2 建立個人化推薦的 Flex Message，每張卡片包含店名、大叔介紹文、地圖按鈕，格式參考 `_build_nearby_flex`；訊息尾端附上 Quick Reply 按鈕「附近巷仔口 🏘️」，行為與附近相似風格的設計一致
- [x] 3.3 在 `handle_location` 新增 `__taste__` session 分支，呼叫比對邏輯並回傳 Flex Message，完成後清除 taste quiz session state
