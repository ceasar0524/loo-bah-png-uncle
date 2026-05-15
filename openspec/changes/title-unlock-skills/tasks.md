## 1. 升級 Flex Message 技能解鎖台詞

- [x] 1.1 新增 `_SKILL_UNLOCK_TEXT` dict，定義每個稱號的技能解鎖台詞（肉盾／絕對滷域／魯拉／滷界敕令）
- [x] 1.2 修改 `_build_upgrade_flex`，在升級 Flex body 下方加入技能解鎖台詞區塊（分隔線 + 技能名稱 + 說明文字）（升級 Flex Message 修改）
- [x] 1.3 驗證升級至各稱號時，upgrade Flex Message includes skill unlock announcement 正確顯示對應台詞

## 2. 技能權限檢查基礎建設

- [x] 2.1 新增 `_get_user_title_and_count(user_id)` 輔助函式，從 Firestore 一次讀取 `current_title` 與 `unique_count` 並回傳（設計：技能權限檢查方式）
- [x] 2.2 新增 `_check_skill_unlocked(user_title, required_level)` 輔助函式，依 `_TITLE_LEVEL_MAP` 判斷是否達到所需等級
- [x] 2.3 實作 skill lock message for insufficient title：組裝封印訊息，帶入目前稱號、技能名稱、所需差距家數（`required_threshold - current_unique_count`）
- [x] 2.4 擴充 `_sessions` 結構，新增 `skill`、`step`、`data` 欄位，支援多步驟技能的 session 管理（設計：多步驟技能的 Session 管理）

## 3. 肉盾技能實作

- [x] 3.1 新增 `_handle_meat_shield(user_id, user_title)` 函式，處理肉盾發動流程（meat shield activation）
- [x] 3.2 實作 fuzzy store name matching：子字串比對 `_store_notes` 和 `_hidden_gems`，單一結果直接判定，多結果列出讓用戶選（設計：肉盾模糊比對）
- [x] 3.3 實作 meat shield evaluation with taste profile：讀取用戶口味偏好，計算符合屬性數量，回傳 🟢🟡🔴 verdict（設計：肉盾口味判定邏輯）
- [x] 3.4 實作 meat shield evaluation without taste profile：無口味偏好時回傳店家資訊並引導填寫
- [x] 3.5 在 `line-bot-webhook` 文字事件加入「肉盾」觸發器（肉盾 text trigger），依等級分派或回覆未解鎖提示

## 4. 魯拉技能實作

- [x] 4.1 新增 `_handle_lura(user_id, user_title)` 函式，回覆「🌀 魯拉發動！」與分類 Quick Reply（lura skill activation）
- [x] 4.2 實作 lura store list by category 分類查詢邏輯（設計：魯拉分類查詢）：最近攻略、最常回訪、好久沒吃各取前 5 筆
- [x] 4.3 實作 Google Maps navigation link：組裝導航 URL，每個店家顯示「前往導航 🗺️」按鈕
- [x] 4.4 在 `line-bot-webhook` 文字事件加入「魯拉」觸發器（魯拉 text trigger），依等級分派或回覆未解鎖提示

## 5. 號令技能實作

- [x] 5.1 設計 Firestore decree data persistence 結構：`decrees/{date}/posts/{user_id}`（設計：號令資料儲存）
- [x] 5.2 新增 `_handle_decree_post(user_id)` 函式，引導大神輸入店名（自由輸入，不限系統店家，≤20字）與理由（≤50字），每日限一次（decree posting for 魯肉飯大神 users）
- [x] 5.2a 實作關鍵字黑名單過濾，觸發時回覆「大叔審核不通過，請重新輸入」（decree posting content moderation）
- [x] 5.3 新增 `_handle_decree_wall(user_id)` 函式，讀取今日所有推薦，每筆顯示 `魯肉飯大神#X-xxxx` 標識（decree wall accessible to all users）
- [x] 5.4 在 `line-bot-webhook` 加入「號令」text trigger：大神進入發令流程，其他用戶查看推薦牆（號令 text trigger）

## 6. 足跡頁面新增絕對滷域按鈕

- [x] 6.1 修改 `_build_footprint_flex`，Lv.2+ 用戶顯示「絕對滷域 🗺️」URI 按鈕（absolute domain map button in footprint，absolute domain button in footprint Flex Message）
- [x] 6.2 低於 Lv.2 用戶不顯示此按鈕（below Lv.2 user footprint excludes map button）

## 7. 絕對滷域 LIFF 地圖頁面

- [x] 7.1 新增後端 endpoint `GET /liff/absolute-domain`，回傳用戶打卡過的店家座標列表（LIFF map page displaying checked-in stores）
- [x] 7.2 建立 LIFF HTML 頁面，使用 Leaflet.js + OpenStreetMap 底圖，標記打卡據點與半透明光暈
- [x] 7.3 在 deploy.yml 新增 `ABSOLUTE_DOMAIN_LIFF_URL` 環境變數，並於 Cloud Run 設定對應 LIFF
- [ ] 7.4 驗證 Lv.2+ 用戶開啟地圖可看到打卡據點，Lv.2 以下看不到地圖入口
