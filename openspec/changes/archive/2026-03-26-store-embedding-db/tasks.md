## 1. 環境與模型載入

- [x] 1.1 確認 CLIP（openai/clip-vit-base-patch32）可正常載入，使用 CLIP（openai/clip-vit-base-patch32）產生 embedding
- [x] 1.2 建立 `modules/embedding_builder.py` 模組結構

## 2. Embedding 建立（embedding-index-builder）

- [x] 2.1 實作 build embedding index from store photos：讀取資料夾結構，對每張 JPEG/PNG 照片產生 CLIP embedding
- [x] 2.2 實作 preprocessing consistency：建索引前對每張照片套用 resize + 亮度標準化，與查詢時前處理一致
- [x] 2.3 實作 unsupported file skipped：非 JPEG/PNG 檔案記錄警告並跳過，不中斷流程（不支援的格式和損壞照片跳過不中斷）
- [x] 2.4 實作 corrupted image skipped：無法讀取的照片記錄警告並跳過，不中斷流程

## 3. KNN 向量儲存（store all photo vectors for KNN matching）

- [x] 3.1 實作 store all photo vectors for KNN matching：儲存所有照片向量供 KNN 比對，不取 centroid，每筆向量附上店家標籤（儲存所有照片向量供 KNN 比對，不取 centroid）
- [x] 3.2 實作 photo_count stored per store：每家店 photo_count 一併存入索引
- [x] 3.3 確認 new store can be appended by rebuilding：新增店家時重建整個索引即可

## 4. 索引持久化

- [x] 4.1 實作 index persisted to disk：以 .npz 格式儲存所有向量、店家標籤、photo_count（索引以 .npz 格式持久化）
- [x] 4.2 確認索引可重新載入，不需重新處理照片

## 5. 摘要與 CLI

- [x] 5.1 實作 index integrity check / build summary reported：建立完成後輸出店家數與照片總數
- [x] 5.2 建立 `build_index.py` entry point：接受資料集目錄路徑，執行完整建索引流程

## 6. 測試

- [x] 6.1 以小型測試資料集（3 家店各 3 張）驗證索引正確建立
- [x] 6.2 確認損壞照片與非圖片檔不會導致程式中斷
