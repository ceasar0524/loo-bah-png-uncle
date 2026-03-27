## Context

魯肉飯辨識器由六個模組組成，其中 visual-recognition → store-matching → uncle-persona 形成主要資料流。若各模組自行定義輸入輸出格式，整合時需要逐一比對，容易出錯。本 change 在實作任何模組之前先定義資料契約。

## Goals / Non-Goals

**Goals:**

- 定義三個核心資料結構，作為所有模組實作的共同依據
- 格式以 Python TypedDict 或 dataclass 為準，確保型別明確

**Non-Goals:**

- 不做序列化（JSON 存檔、資料庫）
- 不做版本控制或向下相容

## Decisions

### 使用 Python TypedDict 定義資料結構

TypedDict 不需要額外依賴，IDE 可提供型別提示，且可直接當作 dict 使用，不需要額外轉換。

替代方案：dataclass 或 Pydantic。否決原因：模組間傳遞的是簡單結構，不需要驗證或序列化，TypedDict 最輕量。

### 信心分數與照片數量作為一等公民欄位

視覺辨識結果包含 `confidence` 欄位，店家比對結果包含 `photo_count` 欄位，讓 uncle-persona 可直接讀取，不需要額外計算。

## Risks / Trade-offs

- **格式變動需同步更新多個模組** → 資料結構變更時，先更新本 change 的 spec，再各模組跟進
