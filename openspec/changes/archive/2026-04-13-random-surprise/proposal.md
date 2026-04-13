## Why

用戶沒有照片可丟時，仍希望獲得附近魯肉飯推薦。目前系統只能在辨識照片後才提供附近推薦，缺乏零門檻入口。

## What Changes

- 新增「隨機驚喜」功能：用戶分享位置後，從附近收錄店家中隨機抽一家推薦
- 不需要照片，直接觸發位置分享即可
- 圖文選單從三格換成六格版型，新增「隨機驚喜 🎲」按鈕

## Capabilities

### New Capabilities

- `random-nearby-recommendation`: 接收用戶位置，從附近收錄店家中隨機抽取一家並回傳推薦結果

### Modified Capabilities

- `nearby-store-search`: 新增隨機抽取模式（現有為風格相近排序模式）
- `line-bot-webhook`: 新增隨機驚喜觸發流程（session 模式 + 六格選單）

## Impact

- Affected specs: `random-nearby-recommendation`（新增）、`nearby-store-search`（delta）、`line-bot-webhook`（delta）
- Affected code: `src/nearby_search/searcher.py`、`src/uncle_persona/persona.py`、`app.py`
