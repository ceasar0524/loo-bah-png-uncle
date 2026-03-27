## 1. 環境與索引載入

- [x] 1.1 建立 `modules/store_matcher.py` 模組結構
- [x] 1.2 實作索引載入：從 .npz 讀取所有向量、店家標籤、photo_count

## 2. KNN 比對（knn-store-matching）

- [x] 2.1 實作 KNN store matching：計算查詢向量與索引所有向量的餘弦相似度，取 top-K（使用 KNN 多數決而非 centroid 餘弦相似度）
- [x] 2.2 實作 store identified by majority vote：K=5 預設，多數決定勝出店家
- [x] 2.3 實作 similarity score computed as average：勝出店家的向量相似度取平均作為分數（相似度以最高票店家的平均相似度回傳）
- [x] 2.4 實作 results ordered by similarity descending：結果按相似度降序排列
- [x] 2.5 實作 similarity threshold filtering：預設門檻 0.5，低於門檻回傳空 list
- [x] 2.6 實作 threshold configurable：支援自訂門檻值
- [x] 2.7 實作 tie detection：top-K 票數平均時回傳 is_tie: true，matches 為空（tie detection）
- [x] 2.8 實作 similarity confidence level：高信心（>=0.8）標記 "high"，中信心（0.5–0.8）標記 "medium"
- [x] 2.9 確認 result conforms to store-matching-schema：回傳包含 is_tie、store_name、similarity、confidence_level、photo_count 的結果

## 3. Leave-one-out Evaluation（leave-one-out-evaluation）

- [x] 3.1 建立 `evaluate.py` entry point
- [x] 3.2 實作 leave-one-out evaluation：逐一排除每張照片當測試，其餘當索引預測（leave-one-out evaluation 作為辨識率基準）
- [x] 3.3 實作 overall accuracy reported：輸出整體辨識率百分比
- [x] 3.4 實作 per-store accuracy reported：輸出各店辨識率，由低至高排列
- [x] 3.5 實作 confusion summary reported：輸出最常混淆的店家組合

## 4. 測試

- [x] 4.1 以小型資料集驗證 KNN 多數決結果正確
- [x] 4.2 確認相似度低於門檻時回傳空 list
- [x] 4.3 跑完整 leave-one-out evaluation，確認輸出格式正確
