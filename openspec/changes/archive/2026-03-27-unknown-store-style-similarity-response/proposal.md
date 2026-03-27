## Why

這個應用的定位是提供有趣回應，而非追求學術級精度。強迫大叔在信心不足時猜出一個店名，反而顯得不自然。改用「風格像 XX 那種路線」的說法，讓大叔保持個性的同時更誠實。

## What Changes

- 信心中等（medium）：不猜具體店名，改說「這碗的風格有點像 XX 那種路線」
- 信心低（low）：不猜，說「大叔沒見過這家，但看起來是...風格」，描述碗的視覺特徵
- 信心高（high）：維持原本行為，直接說出店名

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `uncle-persona-response`: 新增 medium/low 信心時的「風格像」回應規則，取代強猜店名行為

## Impact

- 受影響 spec：`uncle-persona-response`
- 受影響程式碼：`src/uncle_persona/persona.py`
