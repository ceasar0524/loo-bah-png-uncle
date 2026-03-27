## Context

分類器原本回傳兩行文字（yes/no + 0–10 整數）。後來更新為 JSON prompt，單次 call 同時回傳分類與視覺特徵欄位。「Extract visual features in same Haiku call」requirement 記錄了新行為，但原本的分類 requirement 沒有跟著更新。

## Goals / Non-Goals

**Goals:**

- 將原本 requirement 的兩行格式說明替換為 JSON 格式說明
- 保留既有的門檻與邊界情況 scenario（行為不變）

**Non-Goals:**

- 變更分類準確率或門檻邏輯
- 修改視覺特徵提取 requirement（已由獨立 requirement 覆蓋）

## Decisions

**直接 MODIFY 現有 requirement。** 分類契約（門檻、is_lu_rou_fan 語意）不變，只有 prompt/回應格式從兩行文字改為 JSON。更新現有 requirement 可避免與「Extract visual features」requirement 重複。

## Risks / Trade-offs

無。純 spec 與實作同步，不影響行為。
