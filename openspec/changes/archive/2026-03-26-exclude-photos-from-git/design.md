## Context

店家照片是本地訓練資料，不屬於程式碼的一部分。向量索引（index.npz）是由照片產生的衍生檔，已足夠讓系統在無照片的環境下執行 matching。

## Goals / Non-Goals

**Goals:**

- 確保 `photos/` 目錄不被 git 追蹤，防止照片誤上傳

**Non-Goals:**

- 不影響 index.npz 的版控狀態
- 不限制本地開發時的照片存取

## Decisions

### photos/ 加入 .gitignore

在 `.gitignore` 加入 `photos/` 一行即可，無需其他設定。

## Risks / Trade-offs

- [Trade-off] 新開發者 clone 後沒有照片，無法直接重建 index，需另外取得照片 → 可透過 README 說明照片取得方式
