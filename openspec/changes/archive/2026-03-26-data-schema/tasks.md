## 1. 資料結構定義（使用 Python TypedDict 定義資料結構）

- [x] 1.1 建立 `modules/schemas.py`，定義 visual recognition result schema 對應的 TypedDict
- [x] 1.2 定義 store matching result schema 對應的 TypedDict，包含 photo_count 作為一等公民欄位（信心分數與照片數量作為一等公民欄位）
- [x] 1.3 定義 uncle persona input schema 對應的 TypedDict，組合視覺與比對結果

## 2. 驗證

- [x] 2.1 確認 visual recognition result schema：有魯肉飯時所有欄位有值，非魯肉飯時欄位為 None
- [x] 2.2 確認 store matching result schema：結果按相似度降序排列，無符合時回傳空 list
- [x] 2.6 確認 uncle persona input schema：空 matches 與非魯肉飯輸入皆可正常傳入
