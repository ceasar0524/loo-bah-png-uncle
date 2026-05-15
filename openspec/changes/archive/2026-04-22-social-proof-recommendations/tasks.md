## 1. 評價 Firestore 儲存（評價 Firestore 資料結構）

- [x] 1.1 在 webhook handler 新增「必吃 👍」、「普通 😐」、「不能只有我吃到 🤫」訊息處理，依評價選項與語意（必吃 → must_eat、普通 → neutral、不能只有我吃到 → bad）從 session 讀取 `pending_rating`，非同步寫入 `store_ratings/<store_name>/votes/<user_id>`（Rating storage）
- [x] 1.2 確認評分記錄包含 `rating`、`rated_at`、`title`、`title_number` 欄位，重複評價直接覆蓋（Rating storage）

## 2. 評價入口時機（Rating prompt after check-in）

- [x] 2.1 實作 Rating prompt after check-in：打卡確認後，依評價入口時機規則送出評價邀請 Quick Reply，並設定 session `pending_rating`（Rating prompt sent after check-in）
- [x] 2.2 確認評價邀請在升級儀式感訊息之後送出（Rating prompt sent after upgrade ceremony）

## 3. LIFF 評價展示頁（LIFF ratings page）

- [x] 3.1 新增 Flask 路由 `/liff/ratings`，回傳 LIFF HTML 頁面（LIFF ratings page）
- [x] 3.2 新增 Flask 路由 `/api/ratings/<store_name>`，讀取 Firestore must_eat 評價，回傳 JSON（Ratings API endpoint）
- [x] 3.3 LIFF 頁面實作動態效果展示評價代號，無評價時顯示引導文字

## 4. 推薦 Flex Message 加入「查看評價」與「分享」按鈕

- [x] 4.1 隨機驚喜 Flex Message 加入「查看評價 💬」URIAction 按鈕（Social proof LIFF button and weight boost in random recommendation）
- [x] 4.2 個人化推薦 Flex Message 加入「查看評價 💬」URIAction 按鈕（Social proof LIFF button in personal taste recommendation）
- [x] 4.3 巷仔口清單 Flex Message 加入「查看評價 💬」URIAction 按鈕（Social proof LIFF button in hidden gems list）
- [x] 4.4 隨機驚喜 Flex Message 加入「分享這家店 📤」URIAction 按鈕（Share LIFF page）
- [x] 4.5 個人化推薦 Flex Message 加入「分享這家店 📤」URIAction 按鈕（Share LIFF page）
- [x] 4.6 巷仔口清單 Flex Message 加入「分享這家店 📤」URIAction 按鈕（Share LIFF page）
- [x] 4.7 確認 Social proof LIFF button in recommendations 統一套用至所有推薦類型

## 5. 隨機驚喜推薦權重加成（Rating weight boost for random recommendation）

- [x] 5.1 Rating weight boost for random recommendation：修改隨機驚喜抽取邏輯，讀取各候選店家的 `must_eat` 票數，計算加權後以 `random.choices(weights=...)` 抽取（Store has must_eat votes in random draw）<!-- skipped: 改用「N 位同好推薦 🔥」標籤取代隱性加權 -->

## 6. LIFF 分享頁（分享 LIFF 頁面 / Share LIFF page）

- [x] 6.1 新增 Flask 路由 `/liff/share`，回傳 LIFF HTML 頁面；頁面接受 `store`、`lat`、`lng` query 參數，載入後立即呼叫 `liff.shareTargetPicker()` 發送含店家資訊、Google Maps 連結與用戶稱號代號的 Flex Message（Share LIFF page）
- [x] 6.2 新增 Flask 路由 `/api/user-title`，接受 Authorization header 中的 LIFF access token，回傳用戶稱號代號 JSON `{ "title": "...", "title_number": N, "display": "...#N" }`（User title API endpoint）
- [x] 6.3 用戶選完聯絡人後 LIFF 頁面自動關閉；若取消分享亦自動關閉（Share LIFF page）
