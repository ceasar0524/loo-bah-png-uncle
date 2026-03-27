## Context

本模組從 `store-embedding-db` 載入向量索引（所有照片向量 + 店家標籤 + photo_count），對輸入照片做 KNN 比對，回傳符合 `data-schema` 定義的結果。辨識率是系統核心指標，因此本模組也提供 leave-one-out evaluation 讓使用者在實作後即可量化準確度。

## Goals / Non-Goals

**Goals:**

- KNN 多數決比對，K 預設 5，可設定
- 相似度門檻過濾（預設 0.5）
- Leave-one-out evaluation 輸出整體辨識率與混淆矩陣摘要

**Non-Goals:**

- 不做即時重新訓練
- 不做 A/B 測試不同 K 值的自動最佳化

## Decisions

### 使用 KNN 多數決而非 centroid 餘弦相似度

保留所有照片向量，找出最像的 K 張後以多數決定店家。相比 centroid，對少數品質差的照片更有抵抗力。

K=5 為預設值，適合每家店 13~17 張的資料集規模。

### 相似度以最高票店家的平均相似度回傳

多數決後，把屬於勝出店家的那幾張照片的相似度取平均，作為該次比對的相似度分數。這樣比單張最高分更穩定。

### Leave-one-out evaluation 作為辨識率基準

每次留一張照片當測試，其餘當索引，跑完所有照片算整體辨識率。同時輸出哪些店最常被混淆，讓使用者知道哪裡需要補充照片。

## Risks / Trade-offs

- **K 值影響辨識率** → 預設 K=5，使用者可透過 evaluation 結果調整
- **索引規模增大時速度變慢** → 目前數百張 numpy 線性搜尋夠快，未來店家大幅增加再考慮 FAISS
