## 1. 附近搜尋新增隨機抽取模式

- [x] 1.1 隨機抽取邏輯放在 `nearby_search/searcher.py`：新增 `search_random_nearby_store(lat, lng, store_notes)` 函式（Random nearby store recommendation、random nearby store search mode）
- [x] 1.2 在 `src/nearby_search/__init__.py` 匯出 `search_random_nearby_store`

## 2. Persona 新增隨機驚喜回應

- [x] 2.1 `persona.py` 新增 `generate_random` 方法：產生「大叔今天幫你決定」風格回應，顯示店家風格簡介（random recommendation response format）

## 3. app.py 整合

- [x] 3.1 關鍵字「隨機驚喜」觸發 QuickReply 位置分享：在 `handle_text` 新增處理，回傳引導訊息 + QuickReply 位置按鈕（random surprise trigger via text keyword）
- [x] 3.2 session 模式用字串標記區分：定義 `_RANDOM_SESSION = "__random__"` 常數，在 3.1 儲存此值至 session
- [x] 3.3 在 `handle_location` 依 session 值分支：`"__random__"` 走 `search_random_nearby_store` + `generate_random`，store name 走現有流程（handle location message）

## 4. LINE 圖文選單版型更換（手動）

- [x] 4.1 圖文選單換為六格版型（手動）：在 LINE OA 後台新增「隨機驚喜 🎲」按鈕，action 設為傳送文字「隨機驚喜」
