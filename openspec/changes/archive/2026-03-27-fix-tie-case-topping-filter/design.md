## Context

`persona.py` 的 `_format_input` 在平手情境下，透過各平手店家的 `known_toppings` 合集來做配料過濾。若合集為空，原本直接信任 Haiku 偵測結果——導致 Haiku 誤判的配料出現在回應中。

## Goals / Non-Goals

**Goals:**

- 所有平手店家 `known_toppings` 確認為空時，阻止 Haiku 誤判配料出現在回應中
- 保留平手店家有非空 `known_toppings` 時的歸屬標注邏輯（「若是XX那碗：可能有YY」）
- 保留對完全無 store_notes 的店家退回信任 Haiku 的行為

**Non-Goals:**

- 變更配料偵測準確率（屬於分類器問題）
- 修改單一店家（非平手）的配料過濾路徑

## Decisions

**在迭代平手店家時追蹤 `all_have_notes` 旗標。** 若某店家在 `store_notes` 中不存在，設 `all_have_notes = False`。迭代結束後：
- `tie_topping_owners` 有內容 → 設 `known_toppings` 為其 key 列表（原本行為）
- `tie_topping_owners` 為空且 `all_have_notes` 為 True → 設 `known_toppings = []`（新增：過濾所有偵測到的配料）
- `tie_topping_owners` 為空且有店家缺 notes → 維持 `known_toppings = None`（原本行為：退回信任 Haiku）

此設計區分「已知店家但無特殊配料」與「完全不知道的店家」。

## Risks / Trade-offs

- 若某店家實際上有配料但未登錄在 `known_toppings`，該配料會被過濾掉。這是預期的保守行為——只說有根據的。
- 單一店家（非平手）路徑不受影響。
