## 1. Spec 更新（已完成，無實作異動）

- [x] 1.1 更新 visual-recognition-schema：VisualResult 新增 bowl_color、bowl_shape、bowl_texture 欄位，更新 non-lu-rou-fan fallback 說明
- [x] 1.2 更新 visual-feature-recognizer：「偵測配料」改為 Haiku 提取（CLIP 配料偵測已被取代）；pork_part、fat_ratio、skin、sauce_color、rice_quality 保留 CLIP 但用途僅限大叔描述，不用於店家比對
- [x] 1.3 更新 end-to-end-pipeline：補充 store_notes_path 參數說明，新增 Haiku override 串接步驟與 store_notes 不存在時的 fallback scenario
