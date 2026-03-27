## Why

store-embedding-db 建立索引和 visual-recognition 查詢時各自對照片做前處理，若兩邊步驟不一致，向量就不在同一空間，比對結果會失準。需要一個共用的前處理模組確保一致性。

## What Changes

- 新增共用前處理函式：resize 到最大 1024px（保持比例）、亮度正規化
- store-embedding-db 和 visual-recognition 均呼叫此模組，不自行實作前處理
- 支援 JPEG 與 PNG，跳過無法讀取的檔案並記錄警告

## Capabilities

### New Capabilities

- `image-preprocessor`: 共用前處理管線，提供 resize + 亮度正規化，供 index 建立與查詢時統一呼叫

### Modified Capabilities

(none)

## Impact

- Affected specs: `image-preprocessor`
- Affected code:
  - `src/preprocessing/preprocessor.py`
  - `src/preprocessing/__init__.py`
- Consumed by: `store-embedding-db`、`visual-recognition`
