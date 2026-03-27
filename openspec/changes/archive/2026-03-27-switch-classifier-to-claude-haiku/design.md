## Context

目前 `src/visual_recognition/classifier.py` 使用 CLIP zero-shot 進行魯肉飯辨識，流程為：
1. 麵條偵測 gate（binary softmax）
2. 正向/負向提示詞 softmax 取得 confidence

實測 122 張訓練照片，通過率 70.5%（CLIP 的 zero-shot 對台灣在地食物特徵辨識不足）。
改用 Claude Haiku vision 後，通過率提升至 92%（103/112）。

## Goals / Non-Goals

**Goals:**
- 以 Claude Haiku vision API 取代 CLIP 作為 `classify()` 的後端
- 維持 `classify(pil_image, threshold) → (bool, float)` 的公開介面不變
- 信心值定義為 Haiku 回傳 0–10 整數分數除以 10

**Non-Goals:**
- 不修改 store matching、persona 等其他模組
- 不移除 `src/clip_model.py`（store matching 的 embedding index 仍依賴 CLIP）
- 不調整 `build_index.py` 或 `evaluate.py`

## Decisions

### 使用 Claude Haiku 而非 Sonnet 作為分類器

實測比較三種分類方式（相同 122 張照片，threshold=0.5）：
- CLIP zero-shot：通過 86，誤判 36
- Claude Sonnet：通過 58，誤判 64（過於保守）
- Claude Haiku：通過 100，誤判 22

Haiku 在誤判率和 API 費用之間取得最佳平衡。Sonnet 過於嚴格，CLIP zero-shot 對在地食物辨識不足。

### 預設門檻設為 0.5（對應 Haiku 5/10 分）

Haiku 0–10 分數語意直觀：5 分以上代表「有把握是魯肉飯」。實測 threshold=0.4~0.7 範圍內通過率差異不大，選 0.5 作為中間值。

### PIL Image → base64 JPEG 傳送

`_client.messages.create()` 使用 base64 image source。轉換方式：`PIL → BytesIO → base64`，格式固定為 JPEG（壓縮率高，對食物照片品質足夠）。

### answer=="yes" AND confidence>=threshold 雙重條件

防止 Haiku 回答「no」但給高分的矛盾情況（實測有出現）。兩個條件都必須成立才判定為魯肉飯。

## Risks / Trade-offs

- **API 費用**：每張照片呼叫一次 Claude API，批次測試 100+ 張有費用。→ 僅在需要時執行，不做 real-time 以外的批次呼叫
- **網路延遲**：比 CLIP 本地推理慢。→ 單張圖片延遲約 1–2 秒，在互動場景可接受
- **API Key 管理**：需設定 `ANTHROPIC_API_KEY` 環境變數，`.env` 不能進 git。→ `.gitignore` 已排除 `.env`
