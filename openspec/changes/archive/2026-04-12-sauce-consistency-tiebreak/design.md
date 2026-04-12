## Context

目前 KNN 比對的平手解決流程為：
1. CLIP KNN 正規化投票 → 偵測平手（`_TIE_MARGIN = 0.15`）
2. Haiku 碗型 + 配料加分 → 排序後取第一名

當前兩名 Haiku 加分相同（或都沒有明確特徵）時，仍以 CLIP 相似度決勝，準確度不足。

實驗顯示 DINOv2（dinov2_vitb14）對手動裁切的醬汁中心區域能有效區分稠 vs 水兩類，同類平均相似度 0.74、跨類 0.56，完全不重疊，可作為第三層 tie-breaker。

## Goals / Non-Goals

**Goals:**

- 當平手前兩名的 `sauce_consistency` 標記不同時，透過 DINOv2 預測 query 圖的濃稠類別並選出吻合者
- 非平手路徑完全不受影響
- 功能可透過 env var 快速關閉

**Non-Goals:**

- 為所有 23 家店建立濃稠度標記（初始只標記有 reference 照片的 6 家）
- 取代 CLIP 或 Haiku 的角色
- 改動 DINOv2 模型本身

## Decisions

### DINOv2 預測方式：KNN 比對 reference embeddings

query 圖片以 DINOv2 center-crop 轉 embedding，與 `index_dino_crop.npz` 中的 reference embeddings 做 cosine similarity，取 top-K 投票決定稠/水類別。

**為何不用門檻而用 KNN？** reference 樣本少（每家 3 張），投票比固定門檻更穩健。

**為何用 center-crop？** 醬汁區域通常集中於碗中心，center-crop 是最簡單且不需額外偵測的近似裁切方式，與建 index 時一致。

### 啟動條件：前兩名標記不同才啟動

只有當 candidates[0] 和 candidates[1] 的 `sauce_consistency` 欄位存在且不同時，才呼叫 DINOv2 預測。否則直接回傳原排序。

**理由：** DINOv2 推論有延遲，不必要時不觸發。若標記相同或缺失，濃稠度無法作為區分依據。

### 模型載入：lazy init，process 層級快取

DINOv2 模型在第一次需要時載入，並快取於 module-level 變數，避免重複載入。

**風險：** 首次推論需要數秒。可接受，因為此路徑只在平手時觸發。

### 開關：`DINO_TIEBREAK_ENABLED` env var

預設 `false`，測試穩定後再開啟。失敗時 log warning 並 fallback 原排序。

## Risks / Trade-offs

- **DINOv2 載入時間（~2-3 秒）**：首次觸發平手時會有延遲。→ 可接受，平手是少數情況；未來可改為啟動時預載
- **reference 照片只有 6 家**：非這 6 家的候選不會觸發此層。→ 隨著 `photos_sauce_crop` 補充，覆蓋範圍自動擴大
- **center-crop 可能截到碗緣非醬汁區域**：→ 實驗結果顯示仍有效，接受此誤差
- **稠/水兩類標記略為主觀**：→ 目前以實際吃過的判斷為準，後續可調整

## Migration Plan

1. 部署時設 `DINO_TIEBREAK_ENABLED=false`（預設），對現有行為零影響
2. 本地測試確認準確度後，設 `DINO_TIEBREAK_ENABLED=true` 開啟
3. 若線上出現問題，立即設回 `false` rollback
