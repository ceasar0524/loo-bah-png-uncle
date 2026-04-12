## Why

用戶在收到大叔的辨識結果（單一勝出或平手）後，可能想知道「附近還有沒有類似風格的魯肉飯店家」。目前大叔只能回答「這是哪家」，無法幫用戶探索附近的選項。加入附近推薦功能，讓用戶在收到辨識結果後可以主動觸發位置搜尋，找出附近風格相近的店家。

## What Changes

- 大叔回應後新增「找附近類似的 📍」Quick Reply 按鈕
- 用戶點按鈕後，LINE Bot 請用戶分享位置
- 收到位置後，以查詢圖片的 CLIP 向量搜尋風格相近的店家，並依距離篩選
- 大叔以 in-character 方式回應推薦結果
- 若附近無符合店家，大叔誠實告知
- 不影響現有辨識流程——不點按鈕則與現在完全相同

## Capabilities

### New Capabilities

- `nearby-store-search`: 依 CLIP 向量相似度 + 用戶位置，搜尋附近風格相近的店家並排序

### Modified Capabilities

- `line-bot-webhook`: 新增 Quick Reply 按鈕觸發、位置訊息處理流程
- `uncle-persona-response`: 新增附近推薦的回應格式（in-character）

## Impact

- 新增欄位：`data/store_notes.json` 各店家加入經緯度（`location.lat`、`location.lng`）
- 新增欄位：`data/store_notes.json` 各店家加入 `available_toppings`（已存在本機，尚未 commit）
- 受影響程式碼：`app.py`、`src/uncle_persona/persona.py`、`data/store_notes.json`
- 新增模組：`src/nearby_search/`
- LINE Bot 需要處理位置訊息類型（`location` message type）
