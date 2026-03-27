## Context

`visual-profile-and-store-guess-confidence` 封存時，新增了 `lu-rou-fan-classifier` 的視覺特徵提取需求與 `knn-store-matching` 的 Haiku override 機制，但資料結構 spec、特徵辨識 spec 和 pipeline spec 未同步更新。

## Goals / Non-Goals

**Goals:**

- 將 `visual-recognition-schema`、`visual-feature-recognizer`、`end-to-end-pipeline` 三個 spec 同步到目前實作狀態
- 純 spec 更新，不異動程式碼

**Non-Goals:**

- 變更任何實作行為
- 更新其他已對齊的 spec

## Decisions

**三個 spec 各自用 MODIFIED 更新對應的 requirement**。每個 spec 各有一個需要更新的 requirement block，更新現有內容即可，不需要新增 requirement。

- `visual-recognition-schema`：在 VisualResult 欄位列表加入 bowl_color、bowl_shape、bowl_texture，更新 non-lu-rou-fan fallback 說明
- `visual-feature-recognizer`：更新「偵測配料」requirement 描述為 Haiku 提取碗特徵與配料（CLIP 配料偵測已被取代）；CLIP 仍負責 pork_part、fat_ratio、skin、sauce_color、rice_quality，但用途僅限大叔食物描述，不用於店家比對
- `end-to-end-pipeline`：在 pipeline 主流程 requirement 中補充 store_notes_path 參數與 Haiku override 串接步驟

## Risks / Trade-offs

無。純 spec 補記，不影響實作行為。
