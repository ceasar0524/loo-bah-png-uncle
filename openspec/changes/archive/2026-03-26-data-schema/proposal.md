## Why

各模組（visual-recognition、store-matching、uncle-persona）之間的資料格式若各自定義，實作時容易對不上。本 change 統一定義所有模組間的資料契約，作為整個系統的共用介面規範。

## What Changes

- 新增視覺辨識結果的標準資料格式（含 is_lu_rou_fan、配料、肉切法、滷汁、米飯、信心分數）
- 新增店家比對結果的標準資料格式（含店家名稱、相似度、照片數量）
- 新增大叔 persona 模組的輸入格式定義（組合以上兩者）

## Capabilities

### New Capabilities

- `visual-recognition-schema`: 視覺辨識模組輸出的資料結構定義
- `store-matching-schema`: 店家比對模組輸出的資料結構定義
- `uncle-persona-input-schema`: 大叔 persona 模組接收的輸入資料結構定義

### Modified Capabilities

（無）

## Impact

- 受影響模組：visual-recognition、store-matching、uncle-persona
- 無外部依賴，純資料契約定義
