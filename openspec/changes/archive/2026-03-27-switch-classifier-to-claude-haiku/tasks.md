## 1. 替換分類後端

- [x] 1.1 移除 classifier.py 中的 CLIP zero-shot 邏輯（正向/負向提示詞 softmax）及 noodle detection gate，改用 Claude Haiku vision API 實作「classify image as lu-rou-fan using CLIP zero-shot」需求（已完成替換）
- [x] 1.2 實作 PIL Image → base64 JPEG 傳送：將 PIL Image 轉換為 BytesIO JPEG，以 base64 編碼後傳給 `claude-haiku-4-5-20251001` 模型（使用 Claude Haiku 而非 Sonnet 作為分類器）
- [x] 1.3 解析模型回傳格式：第一行 yes/no、第二行 0–10 整數信心分數，實作「return confidence score」需求（分數除以 10 正規化為 0.0–1.0）
- [x] 1.4 實作 answer=="yes" and confidence>=threshold 雙重條件判斷，處理「contradictory model response rejected」情境
- [x] 1.5 設定預設門檻設為 0.5（對應 haiku 5/10 分），保持「threshold configurable」介面不變

## 2. 驗證與測試

- [x] 2.1 確認 `classify(pil_image, threshold) → (bool, float)` 公開介面未改變（使用 Claude Haiku 而非 Sonnet 的決策依據）
- [x] 2.2 以實際魯肉飯照片手動驗證分類正確（non-lu-rou-fan image rejected 情境）
- [x] 2.3 確認 `ANTHROPIC_API_KEY` 透過環境變數注入，`.env` 不進 git（API Key 管理風險緩解）
