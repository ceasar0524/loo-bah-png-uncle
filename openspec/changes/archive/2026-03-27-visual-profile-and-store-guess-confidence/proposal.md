## Why

純 CLIP 店家比對準確率約 48.3%，上限受限於大多數魯肉飯照片外觀相近。透過兩項強化：（1）分類時一併提取碗色與香菜等特徵，以 Haiku 覆蓋機制改善有明確視覺特徵店家的比對準確率；（2）大叔猜店語氣依信心分級，讓使用者對辨識結果有合理期望。

## What Changes

- `lu-rou-fan-classifier`：Haiku 單次 call 同時完成「是否魯肉飯」分類 + 視覺特徵提取（碗色、碗形、碗質感、配料）
- `knn-store-matching`：CLIP KNN 為主要比對；若 Haiku 偵測到高信心明確特徵（特殊碗色、香菜），以 Haiku 結果覆蓋 CLIP
- `uncle-persona-response`：猜店語氣依信心分兩檔——明確特徵命中或相似度高時口吻肯定，否則明確說「大叔在猜、可能猜錯」

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `lu-rou-fan-classifier`：分類與特徵提取合併為單次 Haiku call，輸出新增 `bowl_color`、`bowl_shape`、`bowl_texture`、`toppings`
- `knn-store-matching`：新增 Haiku 高信心特徵覆蓋機制（碗色、香菜）
- `uncle-persona-response`：猜店信心分級語氣規則

## Impact

- 修改 specs：`lu-rou-fan-classifier`、`knn-store-matching`、`uncle-persona-response`
- 修改程式：`src/visual_recognition/classifier.py`、`src/store_matching/matcher.py`、`src/uncle_persona/persona.py`
