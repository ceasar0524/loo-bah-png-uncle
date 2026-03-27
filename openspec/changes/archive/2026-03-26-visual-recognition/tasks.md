## 1. 環境與模組結構

- [x] 1.1 建立 `src/visual_recognition/` 目錄與 `__init__.py`
- [x] 1.2 確認 CLIP 模型（openai/clip-vit-base-patch32）可與 store-embedding-db 共用同一實例，不重複載入

## 2. Lu-rou-fan 分類器

- [x] 2.1 實作「使用 CLIP zero-shot 做視覺辨識，不訓練分類器」：在 `classifier.py` 中載入 CLIP，計算圖片與候選文字提示的 cosine similarity
- [x] 2.2 實作 classify image as lu-rou-fan using CLIP zero-shot：is_lu_rou_fan 判斷邏輯，預設門檻 0.6
- [x] 2.3 實作 return confidence score：回傳 0.0–1.0 的 confidence 值
- [x] 2.4 支援 threshold configurable：門檻可由呼叫端傳入覆蓋預設值
- [x] 2.5 實作 result conforms to visual-recognition-schema：非魯肉飯時所有特徵欄位設為 None

## 3. 視覺特徵辨識器

- [x] 3.1 實作「每個特徵獨立做 zero-shot 分類」：在 `feature_recognizer.py` 建立各特徵的分類函式
- [x] 3.2 實作 detect toppings using binary CLIP classification：針對每種配料做二元有/無判斷，從 toppings config file 載入配料清單
- [x] 3.3 實作「配料辨識使用二元判斷而非多選一」：每種配料使用「有 X / 無 X」文字提示對，可多種同時成立
- [x] 3.4 建立預設 `toppings.yaml` 配料設定檔（cilantro、braised_egg、bamboo_shoots、tofu、pickled_mustard），支援 missing config file falls back to defaults
- [x] 3.5 實作 classify pork part from configurable categories：從 `pork_parts.yaml` 載入類別與提示詞，支援 missing pork part config falls back to defaults，建立預設 `pork_parts.yaml`（belly/fatty/lean/skin_heavy）
- [x] 3.6 實作 classify fat-to-lean ratio from configurable categories：從 `fat_ratio.yaml` 載入類別與提示詞，支援 missing fat ratio config falls back to defaults，建立預設 `fat_ratio.yaml`（fat_heavy/balanced/lean_heavy）
- [x] 3.7 實作 detect pork skin presence from configurable categories：從 `skin.yaml` 載入類別與提示詞，支援 missing skin config falls back to defaults，建立預設 `skin.yaml`（with_skin/no_skin）
- [x] 3.6 實作 classify sauce color from configurable categories：從 `sauce_colors.yaml` 載入類別與提示詞，支援 missing sauce color config falls back to defaults，建立預設 `sauce_colors.yaml`（light/medium/dark/black_gold）
- [x] 3.7 實作 classify rice quality from configurable categories：從 `rice_qualities.yaml` 載入類別與提示詞，支援 missing rice quality config falls back to defaults，建立預設 `rice_qualities.yaml`（fluffy/soft/mushy）
- [x] 3.8 實作 feature recognition only runs on confirmed lu-rou-fan：is_lu_rou_fan 為 false 時跳過所有特徵辨識

## 4. is_lu_rou_fan 門檻設定

- [x] 4.1 實作「is_lu_rou_fan 使用較高門檻（0.6）」：預設門檻設為 0.6，並以常數或設定檔方式管理
- [x] 4.2 同時測試中英文提示詞，取較高信心值（對應「CLIP zero-shot 對台灣食物的英文描述可能偏弱」風險）

## 5. 整合與測試

- [x] 5.1 整合 classifier 與 feature_recognizer，在 `__init__.py` 提供統一入口
- [x] 5.2 用至少 3 張魯肉飯照片和 2 張非魯肉飯照片驗證整體流程
- [x] 5.3 確認輸出格式完全符合 visual-recognition-schema
