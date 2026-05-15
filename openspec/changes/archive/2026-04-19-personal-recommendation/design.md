## Context

現有的隨機驚喜與附近相似風格功能都是被動的（依照照片或隨機）。用戶想要主動表達口味偏好，讓系統推薦最符合的店。`store_notes.json` 裡的 24 家店已有 `visual_profile` 資料（`fat_ratio`、`sauce_consistency`、`sauce_color`、`sauce_taste`），可以直接用於比對。

## Goals / Non-Goals

**Goals:**
- 讓用戶透過四題 Quick Reply 選擇口味偏好
- 依偏好比對 `visual_profile`，結合位置回傳 2–3 家最近且最符合的店
- 流程乾淨，不在對話裡堆疊大量訊息

**Non-Goals:**
- 儲存用戶的長期偏好（每次重新填）
- 納入巷仔口 74 家（無 visual_profile 資料）
- 支援複選或自由文字輸入

## Decisions

### 以四題 Quick Reply 依序收集口味偏好

每題發一則訊息，用戶點選後 bot 收到 postback，存入 session，進入下一題。

| 題次 | 問題 | 選項 | 欄位 |
|------|------|------|------|
| 1 | 肉質偏好？ | 偏肥 / 偏瘦 / 都可以 | `visual_profile.fat_ratio` |
| 2 | 喜歡黏一點？ | 黏黏 / 不黏 / 都可以 | `visual_profile.skin`（with_skin / without_skin） |
| 3 | 滷汁濃稠？ | 稠 / 不稠 / 都可以 | 頂層 `sauce_consistency`（稠/水） |
| 4 | 口味偏好？ | 偏甜（南部）/ 偏鹹（北部）/ 都可以 | `visual_profile.sauce_taste` |

選「都可以」等同不篩選該維度。

### Session 狀態管理

`taste_quiz` 存為 `_sessions[user_id]` dict 裡的獨立 key，與現有的 `store`、`seen`、`expanded` 並列，不互相覆蓋。

結構：`_sessions[user_id]["taste_quiz"] = {"step": 0, "answers": {}}`

- `step`：目前在第幾題（0–3）
- `answers`：已收集的答案，key 為欄位名稱

這樣用戶答題中途丟照片，`_save_session` 只更新 `store`，不影響 `taste_quiz`。反之亦然。

完成四題後，將 `store` 設為 `__taste__`，清除 `taste_quiz` key，等待位置。

新增兩個輔助函式：`_save_taste_quiz(user_id, step, answers)` 和 `_get_taste_quiz(user_id)`，不修改現有 session 函式。

### 大叔風格店家介紹

推薦結果的每家店附上一句大叔風格介紹，由 Claude Haiku 根據 `store_notes.json` 的 `notes` 欄位生成。如果該店有 `available_toppings`，也一併提及可加點的配料。

生成提示：傳入 `notes` 內容與 `available_toppings`，要求用台灣大叔口吻濃縮成一句話（30 字以內）。

### 比對邏輯：加權計分

對每家店計算符合分數（0–4 分），每個維度符合加 1 分，「都可以」視為符合。取分數最高者，同分時以距離近優先。回傳 2–3 家。

### 觸發方式

`handle_text` 新增「個人化」關鍵字，回覆第一題並設定 session。

### 推薦結果尾端：附近巷仔口

推薦結果 Flex Message 尾端附「附近巷仔口 🏘️」Quick Reply 按鈕。按下後觸發「巷仔口」文字，系統以推薦時儲存的位置（`last_location`）查詢 3 公里內的 hidden gems，最多回傳 3 家，依距離排序。

營業狀態從 `store_hours.json` 判斷：打烊的店仍列出但標注「（目前打烊）」並灰化。無時間資料的店一律視為營業中。

若 3 公里內沒有店，回傳「殘念！」提示訊息。

`last_location` 在回覆後清除。若用戶直接輸入「巷仔口」（非從推薦結果跳入），無 `last_location`，走原本各區選單。

### Haiku 介紹解析

Haiku 回傳格式為 `【店名】：介紹文`，解析時同時支援全形冒號「：」與半形冒號「:」，避免只有第一家有介紹的問題。

## Risks / Trade-offs

- **24 家樣本較少** → 附近可能只找到 1 家甚至 0 家符合的店。需要處理結果不足時的 fallback（放寬條件或回傳「附近沒有完全符合的店，以下是最近的幾家」）。
- **four-step 問卷流程較長** → 用戶可能中途放棄。Session 可設定 10 分鐘 timeout 自動清除。
- **`sauce_color` 未納入本次設計** → `visual_profile.sauce_color` 有完整資料（dark / medium / light / black_gold），本次不使用。
