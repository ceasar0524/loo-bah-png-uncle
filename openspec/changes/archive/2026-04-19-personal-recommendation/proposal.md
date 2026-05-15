## Why

使用者目前只能透過丟照片來找相似風格的店，沒有辦法主動表達自己的口味偏好。個人化推薦功能讓用戶可以在不丟照片的情況下，透過選擇口感偏好找到附近最符合的店。

## What Changes

- 新增 Rich Menu「個人化」按鈕觸發口味問卷流程
- 以四題 Quick Reply 依序詢問用戶的口味偏好（肉質、黏稠度、濃稠度、甜鹹）
- 依照用戶選擇比對 `store_notes` 的 `visual_profile`，回傳 2–3 家最近且最符合的店

## Capabilities

### New Capabilities

- `personal-taste-recommendation`: 透過四題 Quick Reply 收集口味偏好，比對 visual_profile，回傳附近最符合的店家清單

### Modified Capabilities

- `line-bot-webhook`: 新增「個人化」關鍵字觸發邏輯與四題問卷 session 狀態管理

## Impact

- Affected specs: `personal-taste-recommendation`（新增）、`line-bot-webhook`（修改）
- Affected code: `app.py`、`data/store_notes.json`
