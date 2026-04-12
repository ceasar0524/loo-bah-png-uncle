## Why

CLIP KNN 平手時，現有的 Haiku 碗型 + 配料加分仍可能無法解決平手，導致最終結果由相似度決定，不夠精準。DINOv2 對手動裁切的醬汁區域能有效區分稠（thick）vs 水（thin）兩類（同類平均 0.74，跨類平均 0.56，不重疊），可作為最後一層 tie-breaker。

## What Changes

- 新增 `sauce_consistency`（稠 / 水）欄位至 `store_notes.json`（初始 6 家）
- 新增 `src/sauce_consistency/` 模組，用 DINOv2 預測 query 圖片的醬汁濃稠類別
- 建立 `index_dino_crop.npz`（已完成）作為 DINOv2 reference embeddings
- 在 `matcher.py` 平手排序後插入濃稠度過濾層：前兩名標記不同時才啟動
- 新增 `DINO_TIEBREAK_ENABLED` env var 控制開關（預設 false）

## Capabilities

### New Capabilities

- `sauce-consistency-tiebreak`: 在 KNN 平手排序後，比對 query 圖片與候選店家的醬汁濃稠度，當前兩名標記不同時選出吻合者

### Modified Capabilities

- `knn-store-matching`: 平手解決流程新增第三層（DINOv2 濃稠度），不影響非平手路徑

## Impact

- Affected specs: `sauce-consistency-tiebreak`（新建），`knn-store-matching`（修改）
- Affected code:
  - `data/store_notes.json`（新增 sauce_consistency 欄位）
  - `src/sauce_consistency/__init__.py`（新模組）
  - `src/sauce_consistency/predictor.py`（DINOv2 預測邏輯）
  - `src/store_matching/matcher.py`（插入濃稠度過濾層）
  - `index_dino_crop.npz`（已存在）
  - `photos/photos_sauce_crop/`（reference 照片，已存在）
