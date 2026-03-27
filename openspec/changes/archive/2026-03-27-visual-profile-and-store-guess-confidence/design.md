## Context

目前 classifier.py 只做是否魯肉飯的分類（Haiku 單次 call），特徵提取（碗色、配料）尚未整合進主流程。matcher.py 是純 CLIP KNN，沒有特徵覆蓋機制。評估結果顯示 CLIP 48.3%，加入碗色 + 香菜覆蓋後提升至 50.0%。

## Goals / Non-Goals

**Goals:**

- 分類與特徵提取合併為單次 Haiku call，不增加 API 呼叫次數
- 將碗色 + 香菜覆蓋邏輯整合進 matcher.py 主流程
- 大叔猜店語氣依信心等級分明

**Non-Goals:**

- 不在 Haiku call 中加入肉型、醬汁顏色等 visual_profile 特徵（評估顯示無助於店家辨識）
- 不修改 CLIP embedding index 或 KNN 核心邏輯
- 不追求突破 55% 的店家比對準確率（照片相似度天花板）

## Decisions

### 合併分類與特徵提取為單次 Haiku call

classifier.py 的 prompt 擴充為同時回傳 JSON 格式（is_lu_rou_fan、confidence、bowl_color、bowl_shape、bowl_texture、toppings）。原本的純文字兩行格式改為 JSON，確保欄位解析穩定。

替代方案：保留分類 call 不動，另外加一次特徵提取 call。
否決原因：多一次 API call 成本加倍，且分類與特徵提取邏輯高度重疊。

### Haiku 覆蓋作為 CLIP 後處理，而非替代

覆蓋邏輯在 CLIP KNN 結果出來後執行：若 Haiku 偵測到高信心明確特徵，覆蓋 CLIP 結果；否則保留 CLIP 結果不動。

替代方案：以 Haiku 特徵加分疊加在 CLIP 正規化票數上。
否決原因：評估顯示加分機制製造過多平手（313 從 77% 掉到 0%），覆蓋機制保護沒有特徵的店不受影響。

### 覆蓋門檻設為 0.5（碗色單一特徵即觸發）

`bright_green`（晴光）、`cilantro`（阿興）等特徵足夠獨特，碗色或香菜單獨命中即可覆蓋。

風險：白碗（北北車）觸發誤判。緩解：`wide_flat_plate` 碗形也需命中，兩個特徵合計才超過門檻。

## Risks / Trade-offs

- [Haiku 誤判碗色] → 覆蓋只針對有 `distinctive: true` 的少數店，降低誤判面積
- [JSON prompt 解析失敗] → 加入 try/except，fallback 回傳 is_lu_rou_fan: false，不影響主流程
- [matcher.py 接收特徵格式變動] → classifier 回傳結果需擴充，pipeline.py 需傳遞特徵給 matcher
