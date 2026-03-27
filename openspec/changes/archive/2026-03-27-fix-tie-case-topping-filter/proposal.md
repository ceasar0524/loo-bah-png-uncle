## Problem

平手比對時，配料過濾邏輯會建立 `tie_topping_owners`（各店已知配料的合集）。若所有平手店家的 `known_toppings` 都是空陣列，`tie_topping_owners` 為空，`known_toppings` 維持 `None` 不更新，程式因此走入「無背景知識」分支，直接信任 Haiku 偵測結果輸出配料——即使沒有任何店家有那些配料。

實例：明志派出所對面魯肉飯與龍記小吃店平手，兩家 `known_toppings` 皆為空。Haiku 誤判照片有滷蛋和醃黃蘿蔔，大叔回應因此捏造了不存在的配料。

## Root Cause

在 `_format_input` 的平手配料邏輯中，以 `tie_topping_owners` 是否為空來判斷「有無背景知識」。但 `tie_topping_owners` 為空可能是兩種情況：
- (a) 有些店家根本沒有 store_notes 資料 → 真的不知道，應信任 Haiku
- (b) 所有店家都有資料但 `known_toppings` 皆為空 → 明確知道這些店沒有特殊配料，Haiku 偵測到的應過濾掉

程式沒有區分這兩種情況。

## Proposed Solution

在迭代平手店家時追蹤 `all_have_notes` 旗標。迭代結束後：
- `tie_topping_owners` 有內容 → 沿用原本邏輯（各店配料歸屬）
- `tie_topping_owners` 為空且 `all_have_notes` 為 True → 設 `known_toppings = []`，過濾掉 Haiku 偵測到的配料
- `tie_topping_owners` 為空且有店家缺 notes → 沿用原本邏輯，退回信任 Haiku

## Success Criteria

- 所有平手店家都有 store_notes 且 `known_toppings` 皆為空時，回應不出現 Haiku 偵測到的配料
- 有店家缺 store_notes（真的不確定）時，仍可輸出 Haiku 偵測到的配料
- 平手店家有非空 `known_toppings` 的情況下，現有歸屬標注邏輯不受影響

## Impact

- 受影響程式碼：`src/uncle_persona/persona.py`（`_format_input` 方法）
