## Why

魯肉飯辨識器需要一個視覺分析模組，能從照片判斷是否為魯肉飯、辨識關鍵配料與視覺特徵，作為 uncle-persona 生成有趣回應的輸入資料。

## What Changes

- 新增 CLIP zero-shot 分類器，判斷照片是否為魯肉飯
- 新增配料辨識，包含香菜、滷蛋、筍乾等常見配料
- 新增肉質切法辨識（塊狀、條狀、絞肉）
- 新增醬汁顏色辨識（深褐、淺褐、偏紅）
- 新增米飯品質辨識（鬆散、黏稠、粒粒分明）
- 辨識結果遵循 data-schema 定義的 visual-recognition-schema

## Capabilities

### New Capabilities

- `lu-rou-fan-classifier`: 使用 CLIP zero-shot 判斷照片是否為魯肉飯，回傳 is_lu_rou_fan 與 confidence
- `visual-feature-recognizer`: 辨識魯肉飯的視覺特徵，包含配料（toppings）、肉質切法（meat_cut）、醬汁顏色（sauce_color）、米飯品質（rice_quality）

### Modified Capabilities

(none)

## Impact

- Affected specs: `lu-rou-fan-classifier`, `visual-feature-recognizer`
- Affected code:
  - `src/visual_recognition/classifier.py`
  - `src/visual_recognition/feature_recognizer.py`
  - `src/visual_recognition/__init__.py`
- Dependencies: openai/clip-vit-base-patch32（與 store-embedding-db 共用同一 CLIP 模型實例）
- Conforms to: `data-schema` change 定義的 `visual-recognition-schema`
