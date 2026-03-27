## Why

店家比對功能需要一個預先建立的向量索引，才能在查詢時快速找出與新照片最相似的店家。本模組負責將 30 家店家的 400+ 張照片轉為 CLIP 向量、計算每家店的代表向量（centroid），並持久化到磁碟供比對模組使用。

## What Changes

- 新增 `build_index.py` script，讀取照片資料集目錄，產生 CLIP embedding 並存檔
- 新增每家店 centroid 計算，以平均向量作為該店的代表 embedding
- 新增索引建立完成後的摘要報告（店家數、照片總數）
- 支援重建索引（重新執行即可覆蓋舊索引）

## Capabilities

### New Capabilities

- `embedding-index-builder`: 從照片資料集目錄建立 CLIP 向量索引並持久化
- `store-centroid`: 計算每家店所有照片的平均向量作為代表 embedding

### Modified Capabilities

（無）

## Impact

- 新增檔案：`build_index.py`、`modules/embedding_builder.py`
- 輸出檔案：`data/store_index.npz`（向量索引）
- 依賴：`torch`、`transformers`（CLIP）、`Pillow`、`numpy`
- 資料依賴：30 家店家照片資料集（按資料夾分類）
