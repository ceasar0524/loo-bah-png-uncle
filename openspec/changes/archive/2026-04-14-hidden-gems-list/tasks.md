## 1. 資料載入

- [x] 1.1 在 `app.py` 啟動時載入 `data/hidden_gems.json`，實作 hidden gems data source（資料從 hidden_gems.json 動態載入）
- [x] 1.2 實作從店名括號中擷取區名的 district extraction from store name 邏輯

## 2. 巷子口觸發與 Quick Reply

- [x] 2.1 在 `app.py` 新增 `elif text == "巷子口":` handler，實作 hidden gems list trigger
- [x] 2.2 實作 `_build_hidden_gems_quick_reply()` 函式，依 `hidden_gems.json` 動態產生 Quick Reply 選區按鈕（Quick Reply 選區，再顯示該區 Flex Message）

## 3. 區域店家 Flex Message

- [x] 3.1 實作 `_build_hidden_gems_flex(district)` 函式，列出該區 hidden gems district store list 店家並附地圖按鈕（地圖連結由座標產生）
- [x] 3.2 Flex Message 底部加入「名單持續擴充中，歡迎推薦！」footer note
- [x] 3.3 在 `app.py` 新增文字 handler，接收 Quick Reply 回傳的區名並觸發 hidden gems district store list Flex Message

## 4. 圖文選單更新

- [x] 4.1 在 LINE Official Account Manager 新增「巷子口」按鈕（觸發文字 `巷子口`），更新 rich menu buttons
