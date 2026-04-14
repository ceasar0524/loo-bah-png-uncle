## Why

使用者想探索在地人才知道的隱藏版好店，但目前 LINE Bot 只收錄大眾已知的魯肉飯名店。「巷子口」功能提供一份策展名單，讓使用者透過圖文選單快速查閱，以區為單位瀏覽這些名不經傳卻頗受在地人喜愛的店家。

## What Changes

- 新增「巷子口」圖文選單按鈕，觸發關鍵字 `巷子口`
- 新增 `data/hidden_gems.json` 作為巷子口店家資料來源（含店名與座標）
- 使用者輸入「巷子口」後，系統以 Quick Reply 列出各區選項
- 使用者選擇某區後，系統回傳該區店家的 Flex Message 清單，每家附地圖按鈕
- 清單底部加註「名單持續擴充中，歡迎推薦！」

## Capabilities

### New Capabilities

- `hidden-gems-list`: 巷子口隱藏版店家清單，支援以 Quick Reply 選區後顯示該區店家 Flex Message

### Modified Capabilities

- `line-rich-menu`: 新增「巷子口」按鈕（觸發文字 `巷子口`）

## Impact

- Affected specs: `hidden-gems-list`（新）、`line-rich-menu`（修改）
- Affected code: `app.py`、`data/hidden_gems.json`
