## Why

系統將牛肉麵等有麵條的食物誤判為魯肉飯、store matching 的平手條件太嚴導致明顯相似的兩家無法觸發平手邏輯、平手時大叔誤報 CLIP 幻覺出的配料。需要修正這三個互相關聯的正確性問題。

## What Changes

- **lu-rou-fan-classifier**：在正向/負向 softmax 之前新增麵條偵測 gate；偵測到麵條則直接回傳 `is_lu_rou_fan=False`，不進行後續比較
- **knn-store-matching**：新增 `tie_margin` 參數（預設 0.15）；正規化票數差距在此範圍內即視為平手，不再要求完全相等
- **uncle-persona-response**：`is_lu_rou_fan=False` 時直接回傳固定文字，不呼叫 Claude API；平手時對所有候選店家的 `known_toppings` 取交集，過濾 CLIP 誤報的配料

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `lu-rou-fan-classifier`：新增麵條偵測 gate 作為分類前置條件
- `knn-store-matching`：平手判定從嚴格相等改為容差範圍比較
- `uncle-persona-response`：非魯肉飯時 hardcode 回應；平手配料過濾邏輯改為交集

## Impact

- Affected specs: `lu-rou-fan-classifier`, `knn-store-matching`, `uncle-persona-response`
- Affected code:
  - `src/visual_recognition/classifier.py`
  - `src/store_matching/matcher.py`
  - `src/uncle_persona/persona.py`
