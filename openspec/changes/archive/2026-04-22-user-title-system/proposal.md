## Why

足跡打卡累積後缺乏成就感回饋，用戶沒有動力持續打卡。稱號系統讓打卡數轉化為具體的身份認同，升級時大叔給予儀式感回應，強化用戶持續回訪的動機。

## What Changes

- 依打卡家數解鎖稱號：新手（0–4）→ 老饕（5–14）→ 達人（15+）
- 系統自動產生代號（稱號 + 編號），例如「老饕#47」
- 用戶升級時大叔給予特別的儀式感回應
- 用戶輸入「我的代號」可查詢目前稱號、代號與升級進度
- 足跡 Flex Message 加入稱號與代號顯示

## Capabilities

### New Capabilities

- `user-title-system`: 依打卡數計算稱號、自動產生代號、升級事件偵測與儀式感回應、代號查詢

### Modified Capabilities

- `luroufan-footprint`: 足跡查詢 Flex Message 加入稱號與代號欄位

## Impact

- Affected specs: `user-title-system`（新增）、`luroufan-footprint`（修改）
- Affected code: `app.py`、Firestore `user_footprint/<user_id>` 文件加入 `title`、`title_number` 欄位
