## 1. 平手配料過濾修正（persona.py）

- [x] 1.1 在 `_format_input` 的平手配料邏輯中，追蹤 `all_have_notes` 旗標；若所有平手店家都有 store_notes 資料但合併後 `known_toppings` 為空，設 `known_toppings = []` 以過濾 Haiku 偵測到的配料，而非退回信任 Haiku（對應 spec：Scenario: Tie with known_toppings union empty）
