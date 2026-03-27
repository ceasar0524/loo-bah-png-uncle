## Why

`visual-profile-and-store-guess-confidence` 封存後，有三個 spec 沒有跟著更新，導致 spec 與實作不符：

1. **visual-recognition-schema**：`VisualResult` 缺少 `bowl_color`、`bowl_shape`、`bowl_texture` 三個新欄位
2. **visual-feature-recognizer**：仍描述舊的全 CLIP 架構，未反映現在 Haiku 負責碗特徵與配料、CLIP 負責肉型醬汁的分工
3. **end-to-end-pipeline**：未記錄新增的 `store_notes_path` 參數，也未描述 pipeline 從 VisualResult 取碗特徵傳給 matcher 的 Haiku override 串接步驟

## What Changes

- `visual-recognition-schema`：新增 `bowl_color`、`bowl_shape`、`bowl_texture` 欄位說明及 non-lu-rou-fan 時的 fallback 規則
- `visual-feature-recognizer`：更新為雙階段特徵提取架構（Haiku → 碗特徵 + 配料；CLIP → 肉型、醬汁、豬皮、米飯）
- `end-to-end-pipeline`：補充 `store_notes_path` 參數說明，以及 pipeline 載入 store_notes 並將碗特徵傳給 match_store 的步驟

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `visual-recognition-schema`：VisualResult schema 新增碗特徵欄位
- `visual-feature-recognizer`：特徵提取架構從全 CLIP 更新為 Haiku + CLIP 混合
- `end-to-end-pipeline`：pipeline 介面新增 store_notes_path 參數與 Haiku override 串接

## Impact

- 受影響 spec：visual-recognition-schema、visual-feature-recognizer、end-to-end-pipeline
- 受影響程式碼：`src/schemas.py`、`src/visual_recognition/recognizer.py`、`src/pipeline.py`（已更新，此次僅補 spec）
