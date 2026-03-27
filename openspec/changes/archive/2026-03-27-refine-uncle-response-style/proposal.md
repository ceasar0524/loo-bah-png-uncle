## Why

實際測試發現大叔回應有兩個問題：每次都以「哎唷」開頭，顯得像固定罐頭回應；偶爾出現與食物完全無關的意象（如「在海邊奔跑」），缺乏規範導致出現頻率不當。

## What Changes

- 禁止每次都用相同開場白（特別是「哎唷」），要求開頭有變化
- 明確規範天外飛來一筆的比喻：偶爾可以出現，但不能每次都這樣

## Capabilities

### New Capabilities

（none）

### Modified Capabilities

- `uncle-persona-response`：新增開場白變化規則、比喻使用頻率規範

## Impact

- 修改：`src/uncle_persona/persona.py`（system prompt）
