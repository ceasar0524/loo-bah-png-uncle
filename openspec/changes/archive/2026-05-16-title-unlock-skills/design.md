## Context

目前稱號系統（`_TITLE_THRESHOLDS`、`_build_upgrade_flex`）已可正確判斷等級並在升級時顯示 Flex Message，但升級後沒有任何功能差異。本次新增四個技能，每個技能需要獨立的觸發流程、權限檢查，以及部分需要新 LIFF 頁面。

現有相關函式：
- `_get_title(unique_count)` — 取得當前稱號
- `_build_upgrade_flex(old, new, display, text)` — 升級 Flex
- `_build_footprint_flex(user_id)` — 足跡 Flex
- `_store_notes`, `_hidden_gems` — 店家資料

## Goals / Non-Goals

**Goals:**
- 四個技能依稱號等級解鎖，低等級用戶觸發時收到未解鎖提示
- 升級 Flex Message 新增技能解鎖台詞區塊
- 足跡頁面新增「絕對滷域」按鈕（Lv.2+）
- 肉盾：模糊比對店名 + 依口味偏好判定
- 魯拉：依最近/最常/好久分類顯示打卡過的店 + 導航連結
- 號令：大神發令 + 所有用戶可查看推薦牆
- 絕對滷域：LIFF 地圖頁面（真實地圖 + 打卡據點 + 光暈）

**Non-Goals:**
- RPG 風格自繪地圖（絕對滷域未來可升級，本次用真實地圖）
- 推薦牆的攻略理由不做固定選項（暫定自由輸入，之後再調整）
- 肉盾不支援非魯肉飯類別店家

## Decisions

### 技能權限檢查方式

從 Firestore `user_footprint/<user_id>` 讀取 `current_title` 與 `unique_count`（打卡唯一家數），對照 `_TITLE_LEVEL_MAP` 判斷是否達到所需等級。每個技能觸發時都執行一次權限檢查。

`_get_user_title_and_count(user_id)` 一次回傳 `(current_title, unique_count)`，讓封印訊息可以直接計算「還差 N 家」（`required_threshold - unique_count`）。

**替代方案考慮**：快取 title 在 session — 捨棄，因為 title 可能在當前對話中升級，讀 Firestore 確保準確。

### 肉盾模糊比對

使用簡單子字串比對（`query in store_name` 或 `store_name in query`），不引入外部模糊比對套件。比對範圍涵蓋 `_store_notes` 和 `_hidden_gems`。

**替代方案考慮**：difflib.SequenceMatcher — 可行但引入複雜度，子字串已足夠應付中文店名輸入習慣。

### 肉盾口味判定邏輯

比對店家屬性（fat_level, sauce, saltiness, stickiness）與用戶偏好（從 Firestore `user_preferences/<user_id>` 讀取）。計算符合屬性數量：
- 4/4 或 3/4 符合 → 🟢 適合衝
- 2/4 符合 → 🟡 可以試
- 0/4 或 1/4 符合 → 🔴 小心踩雷

### 魯拉分類查詢

從 Firestore `user_footprint/<user_id>/records` 讀取所有打卡記錄：
- **最近攻略**：依 `checked_in_at` 降序，取前 5 筆唯一店家
- **最常回訪**：按 `store_name` 計數，取前 5 高的
- **好久沒吃**：按 `store_name` 取最後一次打卡，按時間升序，取最舊的 5 筆

導航連結格式：`https://www.google.com/maps/dir/?api=1&destination={lat},{lng}`

### 號令資料儲存

Firestore collection `decrees`，document ID 為日期字串（`YYYY-MM-DD` Taiwan time），subcollection `posts`，document ID 為 `user_id`。

每日限制：讀取 `decrees/{today}/posts/{user_id}` 是否存在來判斷。

### 多步驟技能的 Session 管理

現有 `_sessions` 結構為 `{"store": str, "ts": float, "seen": set}`，針對辨識/隨機驚喜設計，不足以支援多步驟技能流程。

新技能（肉盾、魯拉、號令）各自需要不同的步驟狀態，採用擴充 session 結構的方式，新增 `skill` 和 `step` 欄位：

```python
_sessions[user_id] = {
    "skill": "meat_shield" | "lura" | "decree",  # 當前進行中的技能
    "step": str,       # 當前步驟，例如 "await_store_name"、"await_reason"
    "data": dict,      # 中間資料，例如 {"candidates": [...], "store": "..."}
    "ts": float,       # timestamp，沿用 _SESSION_TTL = 300 秒
    # 以下為既有欄位，保持相容
    "store": str | None,
    "seen": set,
}
```

各技能的步驟定義：

**肉盾**
- `await_store_name`：等待用戶輸入店名
- `await_store_select`：比對到多家，等待用戶選擇（`data["candidates"]` 存候選清單）

**魯拉**
- `await_category`：等待用戶選擇分類（Quick Reply 發出後）

**號令**（僅大神）
- `await_store_name`：等待輸入推薦店名
- `await_reason`：等待輸入推薦理由（`data["store_name"]` 存已輸入的店名）

當用戶觸發新技能時，原有 session 會被覆蓋。TTL 到期後 session 自動清除，用戶需重新觸發技能。

**替代方案考慮**：為每個技能建立獨立的 dict — 捨棄，增加複雜度且難以統一 TTL 管理，擴充現有結構更簡單。

### 升級 Flex Message 修改

在現有 `_build_upgrade_flex` 的 body 區塊下方新增一個技能解鎖區塊（分隔線 + 技能名稱 + 說明文字）。定義 `_SKILL_UNLOCK_TEXT` dict 對應每個稱號的解鎖台詞。

### 絕對滷域 LIFF

新建一個獨立 HTML 頁面，使用 Leaflet.js（不需要 Google Maps API key）：
- 底圖：OpenStreetMap
- 從後端 API endpoint 取得用戶打卡過的店家座標清單
- 每個據點用自訂 icon 標記
- 每個據點畫半透明圓形 circle（radius 約 300m）

新增後端 endpoint：`GET /liff/absolute-domain?user_id=...` 回傳用戶打卡過的店家座標列表（需驗證 LIFF token）。

## Risks / Trade-offs

- **Firestore 讀取次數增加**：肉盾、魯拉每次觸發都需讀取 Firestore。目前用戶數（204）可接受，未來需關注。
- **絕對滷域需要新增 LIFF 及後端 endpoint**，工程量比其他技能大，建議最後實作。
- **肉盾子字串比對**可能在店名很長時漏掉部分輸入，可觀察用戶行為後再調整。

## Open Questions

- 號令的「攻略理由」是自由輸入還是固定選項？（目前暫定自由輸入）
- 大神推薦牆是否要顯示歷史推薦（不只今天）？（目前暫定只顯示今天）
- 絕對滷域的 LIFF 環境變數名稱待定（需在 deploy.yml 新增）
