## 1. 資料準備

- [x] 1.1 在 `store_notes.json` 的 6 家店（啊興阿、雙胖子、天天利、玉女號、阿英、小王）加入 `sauce_consistency` 欄位（稠/水），對應 `photos_sauce_crop` 的分類標記

## 2. DINOv2 預測模組

- [x] 2.1 建立 `src/sauce_consistency/__init__.py` 匯出 `predict_consistency`
- [x] 2.2 建立 `src/sauce_consistency/predictor.py`：實作「predict sauce consistency from query image」，使用 DINOv2 center-crop embedding（設計決策：DINOv2 預測方式：KNN 比對 reference embeddings）+ top-K 投票，模型使用 lazy init process 層級快取（設計決策：模型載入：lazy init，process 層級快取），讀 `index_sauce_crop.npz`；預測失敗回傳 `None`

## 3. Matcher 整合

- [x] 3.1 在 `matcher.py` tie detection 平手候選排序後，實作「sauce consistency tiebreak in store matching」：讀取 `DINO_TIEBREAK_ENABLED` env var（設計決策：開關：`DINO_TIEBREAK_ENABLED` env var），當啟動條件：前兩名標記不同才啟動（設計決策）且預測非 None 時，將吻合者提至第一名；任何條件不符則保持原排序不變（non-tie 路徑不受影響）

## 4. Pipeline 串接

- [x] 4.1 在 `pipeline.py` 平手路徑中，將 `pil_img` 傳入 matcher 供 sauce consistency tiebreak 使用；確認 DINOv2 lazy init 不影響啟動時間

## 5. 測試驗證

- [x] 5.1 本地手動測試：丟一張稠風格照片，確認 tiebreak 啟動後結果正確
- [x] 5.2 確認 `DINO_TIEBREAK_ENABLED=false`（預設）時完全不觸發 DINOv2，原有 tie detection 流程無任何改變
