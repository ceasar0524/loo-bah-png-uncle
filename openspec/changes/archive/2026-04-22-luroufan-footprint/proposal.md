## Why

用戶使用 bot 後缺乏持續回訪的動機，2-4 次互動後就不再使用。透過魯肉飯足跡打卡，讓用戶每次去吃魯肉飯都有理由打開 bot，建立長期使用習慣。

## What Changes

- 照片辨識成功後新增「就是這家嗎？✅ / 不對」確認步驟，確認後記錄打卡
- 辨識平手或失敗時，引導用戶分享位置 → 列出附近店家 → 選一家記錄
- 用戶輸入「足跡」可查看打卡記錄（吃過幾家、哪些店、最近一次）
- 打卡資料儲存至 Firestore `user_footprint/<user_id>`
- 打卡範圍涵蓋 `store_notes`（24 家）與 `hidden_gems`（74 家）共 96 家（扣除 2 組重複店家）

## Capabilities

### New Capabilities

- `luroufan-footprint`: 魯肉飯足跡打卡與查詢功能，包含打卡流程、Firestore 儲存、足跡查詢顯示

### Modified Capabilities

- `line-bot-webhook`: 照片辨識結果後新增打卡確認流程，新增「足跡」關鍵字處理
- `personal-taste-recommendation`: 照片辨識成功/失敗/平手各情境加入打卡入口

## Impact

- Affected specs: `luroufan-footprint`（新增）、`line-bot-webhook`（修改）、`personal-taste-recommendation`（修改）
- Affected code: `app.py`、Firestore `user_footprint` collection
