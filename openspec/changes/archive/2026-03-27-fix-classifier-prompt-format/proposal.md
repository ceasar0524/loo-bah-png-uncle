## Problem

`lu-rou-fan-classifier` spec 仍描述舊的兩行文字格式（第一行 yes/no、第二行 0–10 整數）。實作已更新為單次 JSON 回應，同時回傳分類結果與視覺特徵。spec 與實作不符。

## Root Cause

`visual-profile-and-store-guess-confidence` 封存時，新增了「Extract visual features in same Haiku call」requirement，但沒有 MODIFY 原本「Classify image as lu-rou-fan」requirement，導致舊的兩行格式說明仍留在 spec 中。

## Proposed Solution

MODIFY「Classify image as lu-rou-fan」requirement，將 prompt/回應格式從兩行文字改為 JSON 格式說明：model 回傳包含 `is_lu_rou_fan`、`confidence` 及視覺特徵欄位的 JSON 物件，並補充 JSON 解析失敗時的 fallback scenario。

## Success Criteria

- spec 正確描述目前 JSON-based prompt 與回應格式
- 兩行格式說明從 spec 中移除
- 分類行為相關的既有 scenario（門檻、非食物、矛盾回應）維持有效，並更新為引用 JSON 欄位

## Impact

- 受影響程式碼：`src/visual_recognition/classifier.py`（已更新）
