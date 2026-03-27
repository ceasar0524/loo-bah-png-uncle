## 1. 分類器擴充（classifier.py）

- [x] 1.1 將 classifier.py 的 prompt 改為 JSON 格式，合併分類與特徵提取為單次 Haiku call，輸出 is_lu_rou_fan、confidence、bowl_color、bowl_shape、bowl_texture、toppings（Requirement: Extract visual features in same Haiku call as classification；Decision: 合併分類與特徵提取為單次 Haiku call）
- [x] 1.2 更新 classifier.py 的回傳值，包含 bowl 與 topping 欄位；non-lu-rou-fan 時 bowl 欄位回傳 None、toppings 回傳空 list（Requirement: Bowl features absent for non-lu-rou-fan；Requirement: Single API call for both classification and features）
- [x] 1.3 加入 JSON 解析 try/except，解析失敗時 fallback 回傳 is_lu_rou_fan: false

## 2. 店家比對覆蓋機制（matcher.py）

- [x] 2.1 新增 Haiku feature override 函式：讀取 store_notes.json 的 bowl 與 known_toppings，依碗色、碗形、碗質感、香菜計算覆蓋分數（Requirement: Haiku feature override for high-confidence distinctive features；Decision: Haiku 覆蓋作為 CLIP 後處理，而非替代）
- [x] 2.2 在 match_store 函式加入覆蓋後處理：CLIP KNN 結果完成後執行覆蓋判定，單一店家達門檻才覆蓋，多家達標則抑制覆蓋（Decision: 覆蓋門檻設為 0.5（碗色單一特徵即觸發）；Requirement: Override suppressed when multiple stores qualify）
- [x] 2.3 覆蓋命中時回傳 confidence_level: "high"；無覆蓋時 CLIP 結果不動（Requirement: No distinctive features falls back to CLIP）

## 3. Pipeline 串接

- [x] 3.1 更新 pipeline.py，將 classifier 回傳的 bowl 與 topping 特徵傳遞給 matcher 的 override 機制

## 4. 大叔語氣（persona.py）

- [x] 4.1 在 _format_input 中對 confidence_level "medium" 的店家比對輸出加入「大叔在猜」標記文字，讓 LLM 能依此判斷語氣（Requirement: Store confidence language；Requirement: Medium confidence store match — guessing language required）
- [x] 4.2 在 system prompt 的猜店語氣規則中，明確區分 "high"（肯定語氣，可引用明確特徵）與 "medium"（明確說在猜、可能猜錯）兩種情境（Requirement: Haiku override fires — high confidence language）
