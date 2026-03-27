## Why

有了向量索引之後，需要一個比對模組來回答「這碗魯肉飯最像哪家店」。本模組使用 KNN 多數決比對，從索引中找出最相似的 K 張照片，以多數決決定店家，並提供 leave-one-out evaluation 讓使用者可以實際測量辨識率。

## What Changes

- 新增 KNN 比對功能：載入向量索引，對查詢照片找出最相似的 K 張，多數決定店家
- 新增相似度門檻過濾：低於門檻的結果不回傳
- 新增 leave-one-out evaluation：自動測試辨識率，找出容易混淆的店家

## Capabilities

### New Capabilities

- `knn-store-matching`: KNN 多數決比對，回傳符合 data-schema 的店家結果列表
- `leave-one-out-evaluation`: 自我評估辨識率，輸出整體準確率與各店混淆情況

### Modified Capabilities

（無）

## Impact

- 新增檔案：`modules/store_matcher.py`、`evaluate.py`
- 依賴：`store-embedding-db` 產生的索引、`data-schema` 定義的輸出格式
- 輸入：查詢照片的 CLIP embedding（由 visual-recognition 或直接從照片產生）
- 輸出：符合 `store-matching-schema` 的結果列表
