## 1. Classifier：麵條偵測 Gate

- [x] 1.1 在 `src/visual_recognition/classifier.py` 新增 noodle detection gate：定義麵條正/負向提示詞與 threshold（0.6），實作 `_binary_prob` 輔助函式
- [x] 1.2 修改 `classify()` 函式（Classify image as lu-rou-fan using CLIP zero-shot）：在 positive/negative softmax 前先執行 Noodle detection gate，偵測到麵條時直接回傳 `(False, 1.0 - noodle_prob)`
- [x] 1.3 將預設 threshold 從 0.6 調整為 0.72
- [x] 1.4 驗證：以牛肉麵照片確認 is_lu_rou_fan=False；以魯肉飯照片確認 noodle gate 不誤殺

## 2. Store Matching：Tie Margin 容差設計

- [x] 2.1 在 `src/store_matching/matcher.py` 新增 `_TIE_MARGIN = 0.15` 常數
- [x] 2.2 修改 tie detection 邏輯：由嚴格相等改為 `max_norm_vote - store_norm_vote <= _TIE_MARGIN`
- [x] 2.3 驗證：以明志照片確認與龍記觸發平手（normalized votes 差距 0.10 < 0.15）

## 3. Uncle Persona：非魯肉飯 Hardcode 回應

- [x] 3.1 在 `src/uncle_persona/persona.py` 的 `generate()` 開頭實作 Non-lu-rou-fan input handling：`is_lu_rou_fan=False` 時直接回傳固定文字，不呼叫 Claude API
- [x] 3.2 固定文字為：「所以我說，那個滷肉呢？大叔千里迢迢來鑑定，你給我看這個？」
- [x] 3.3 驗證：以牛肉麵照片確認回傳固定文字且未呼叫 API

## 4. Uncle Persona：平手時 Known Toppings 交集過濾

- [x] 4.1 在 `_format_input()` 中實作 Store background knowledge 平手分支（平手配料過濾：known toppings 交集）：`is_tie=True` 時，取所有候選店家 `known_toppings` 的交集作為過濾條件
- [x] 4.2 僅當所有候選店家都有 `known_toppings` 定義時才套用交集；任一店家缺少記錄則 fallback 信任 CLIP
- [x] 4.3 驗證：以明志照片（平手案例）確認 CLIP 誤報的肉鬆、香菜不出現在大叔回應中

## 5. Index 重建

- [x] 5.1 執行 `python3 build_index.py --photos photos --output index.npz` 將明志加入索引
- [x] 5.2 確認 index 包含 10 家店、明志在其中
