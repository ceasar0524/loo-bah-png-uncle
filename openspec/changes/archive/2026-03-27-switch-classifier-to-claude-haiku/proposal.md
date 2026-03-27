## Why

CLIP zero-shot 分類器在魯肉飯辨識的通過率僅 70.5%（86/122），且對非典型外觀（大塊五花肉、厚醬汁、餐具入鏡）的誤判率高。改用 Claude Haiku vision 後，通過率提升至 92%（103/112），同時原生支援 0–10 信心分數，門檻調整更直觀。

## What Changes

- 移除 CLIP 的正向/負向 softmax 分類邏輯及麵條偵測 gate
- 改用 Claude Haiku (`claude-haiku-4-5-20251001`) 進行 vision 分類
- 模型回傳格式：第一行 `yes`/`no`，第二行 0–10 整數信心分數
- 信心分數正規化為 0.0–1.0，預設門檻從 0.6 改為 0.5
- `classify()` 介面維持不變：`(pil_image, threshold) → (bool, float)`

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `lu-rou-fan-classifier`：後端從 CLIP zero-shot 改為 Claude Haiku vision API；信心值定義從 CLIP softmax 機率改為 Haiku 0–10 分數正規化值；預設門檻從 0.6 改為 0.5

## Impact

- Affected specs: `lu-rou-fan-classifier`
- Affected code: `src/visual_recognition/classifier.py`
- New dependency: `anthropic` Python SDK（呼叫 Claude API）
- 移除 dependency：`torch`（classifier.py 不再使用）、`src/clip_model`（classifier.py 不再直接呼叫）
