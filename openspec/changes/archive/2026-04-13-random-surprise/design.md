## Context

目前系統的附近推薦（`search_nearby_stores`）以風格相近為排序依據，必須先辨識照片才能觸發。用戶若沒有照片、或只是想隨機發現一家附近的店，現有流程無法滿足。

## Goals / Non-Goals

**Goals:**
- 新增隨機抽取模式：從一定半徑內的收錄店家中隨機選一家
- 在 app.py 新增獨立的 session 模式，區分「風格比對」與「隨機驚喜」
- 圖文選單換為六格版型，加入「隨機驚喜 🎲」按鈕（關鍵字觸發）
- persona 新增 `generate_random` 方法產生對應回應

**Non-Goals:**
- 不考慮用戶偏好或歷史紀錄
- 不做排除已推薦過的店家（每次獨立隨機）
- 不修改現有的風格相近推薦流程

## Decisions

### 隨機抽取邏輯放在 `nearby_search/searcher.py`

新增 `search_random_nearby_store(lat, lng)` 函式，從半徑 3km 內的店家中隨機抽一家。若半徑內無店家，擴大至全部店家隨機抽取（保證一定有結果）。

使用獨立函式而非在現有 `search_nearby_stores` 加參數，避免邏輯混雜。

### session 模式用字串標記區分

`_sessions` 現在儲存 `matched_store`（字串）。隨機驚喜需要獨立觸發路徑，用特殊值 `"__random__"` 標記 session，讓 `handle_location` 依據 session 值決定走哪條路。

### 關鍵字「隨機驚喜」觸發 QuickReply 位置分享

`handle_text` 收到「隨機驚喜」後，回傳引導訊息 + QuickReply 位置按鈕，並將 `"__random__"` 存入 session。

### `persona.py` 新增 `generate_random` 方法

隨機驚喜的回應格式參考 `generate_nearby`，但開場白改為強調「大叔幫你決定」的語氣，並顯示店家風格簡介（從 `store_notes` 讀取）。

### 圖文選單換為六格版型（手動）

六格分配：怎麼用 / 店家清單 / 大叔雷達 / 隨機驚喜 / （預留）/ （預留）。版型更換為 LINE OA 後台手動操作，不在程式碼範圍內。

## Risks / Trade-offs

- `"__random__"` 作為 session 標記是 magic string → 若日後新增更多模式需統一改為 enum 或常數。目前只有兩種模式，暫時可接受。
- 隨機驚喜無過濾條件，可能推薦距離較遠的店 → 優先從 3km 內抽，再擴大，降低機率。
