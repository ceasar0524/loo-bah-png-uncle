## Context

目前 LINE Bot 的圖文選單有四個按鈕（怎麼用、店家清單、大叔雷達、隨機驚喜），使用六格版型，尚有空格可加入新按鈕。店家資料分兩份：`data/store_notes.json`（辨識用）與新建的 `data/hidden_gems.json`（巷子口清單用），兩份資料職責明確分開。

## Goals / Non-Goals

**Goals:**

- 使用者點「巷子口」後可瀏覽以區分組的隱藏版店家清單
- 每家店附 Google Maps 地圖連結按鈕
- 清單底部加註持續擴充說明
- 新增店家只需更新 `hidden_gems.json`，不需改程式碼

**Non-Goals:**

- 巷子口店家不納入辨識流程（不用 store_notes.json）
- 不計算與使用者的距離（純靜態清單）
- 不做兩層選單（台北市/新北市分層），等區數夠多再考慮

## Decisions

### Quick Reply 選區，再顯示該區 Flex Message

使用者輸入「巷子口」→ 系統回覆 Quick Reply，每個按鈕是一個區名。使用者點區後傳送該區名文字，系統回傳該區店家的 Flex Message。

選 Quick Reply 而非 Carousel：Carousel 每張卡高度有限，店多時無法全部顯示；Quick Reply 選區後一次展示該區所有店，清楚易讀。

### 地圖連結由座標產生

`hidden_gems.json` 儲存座標，程式碼以 `https://maps.google.com/?q=lat,lng` 產生精準地圖連結。保留座標以供未來加入距離計算功能。

### 資料從 hidden_gems.json 動態載入

啟動時載入 `hidden_gems.json`，與 `store_notes.json` 並行，互不影響。新增店家只需更新 JSON 檔案。

## Risks / Trade-offs

- **Quick Reply 按鈕上限 13 個** → 區數超過 13 時需改兩層選單；目前 9 個區，短期無風險
- **區名文字衝突** → 若「三重區」等文字在其他 handler 被使用到需注意；目前無衝突
