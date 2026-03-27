## 1. 修改 _format_input() 的 tie 配料輸出格式

- [x] 1.1 在 `persona.py` 的 tie 邏輯中，建立「配料 → 擁有該配料的店家」對應表（tie topping attribution），區分共有與獨有配料
- [x] 1.2 共有配料（全部候選店都有）輸出為「兩家都有的配料：XX」格式，作為確定事實（shared toppings）；此即從資料格式而非 prompt 指令強制條件語氣的核心實作
- [x] 1.3 獨有配料（只有部分候選店有）輸出為「若是 XX 那碗：可能有 YY（非確定，視店家而定）」格式（exclusive toppings with store attribution）；system prompt 補充配料標注說明作為雙重保障
- [x] 1.4 非 tie 情境的配料輸出格式維持不變（uncle persona input schema 非 tie 路徑不受影響）

## 2. 更新 system prompt

- [x] 2.1 在 system prompt 的「重要」規則後加入「配料標注說明」：遇到「若是 XX 那碗：可能有 YY」格式時，回應必須使用條件語氣（如果是 XX 的話），不可當成確定事實（store background knowledge conditional language）
