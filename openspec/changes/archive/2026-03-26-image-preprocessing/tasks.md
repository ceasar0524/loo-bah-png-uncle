## 1. 模組結構

- [x] 1.1 建立 `src/preprocessing/` 目錄與 `__init__.py`
- [x] 1.2 建立 `src/preprocessing/preprocessor.py`，提供統一的前處理入口函式

## 2. Resize

- [x] 2.1 實作 resize 上限設為 1024px：長邊超過 1024px 才縮放，保持比例（resize image to maximum 1024px）
- [x] 2.2 確認小於 1024px 的圖片不放大（small image not upscaled）

## 3. 亮度正規化

- [x] 3.1 實作亮度正規化使用直方圖均衡化（CLAHE）：轉換至 LAB 色彩空間，對 L 通道套用 CLAHE（clip_limit=2.0, tileGridSize=8）（brightness normalization using CLAHE）
- [x] 3.2 確認「前處理結果不快取到磁碟」：函式直接回傳處理後的 PIL Image，不寫檔

## 4. 一致性保證

- [x] 4.1 確認 preprocessing pipeline is identical at index build time and query time：store-embedding-db 與 visual-recognition 均 import 並呼叫同一函式，不各自實作

## 5. 錯誤處理

- [x] 5.1 實作 unsupported or corrupted files handled gracefully：無法讀取的檔案回傳 None 並記錄警告，不拋出例外
- [x] 5.2 實作 unsupported format skipped：非 JPEG/PNG 格式回傳 None 並記錄警告

## 6. 整合測試

- [x] 6.1 用同一張照片在 resize + CLAHE 前後各取 CLIP embedding，確認前處理後 embedding 仍在合理範圍（cosine similarity > 0.9）
