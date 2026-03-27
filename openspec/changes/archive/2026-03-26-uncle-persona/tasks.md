## 1. 環境與設定

- [x] 1.1 安裝 `anthropic` Python SDK，確認 Claude API key 環境變數可讀取
- [x] 1.2 建立 `modules/` 與 `examples/` 目錄結構

## 2. Few-shot 範例管理（persona-examples）

- [x] 2.1 建立 `examples/uncle_examples.json`，寫入初始範例（含香菜、滷蛋、無配料等情境），實作 few-shot examples loaded from file
- [x] 2.2 實作 examples path is configurable：模組初始化接受自訂路徑參數
- [x] 2.3 實作 missing examples file falls back to defaults：檔案不存在時使用硬編碼預設範例，不拋出例外（使用 Claude API 搭配 few-shot prompting 實作大叔 persona，few-shot 範例從外部 JSON 檔載入，內建 fallback）

## 3. 大叔 Persona 回應生成（uncle-persona-response）

- [x] 3.1 設計系統 prompt：定義大叔身份、語氣規則、台式用語（哎唷、這款、嘸通等）
- [x] 3.2 實作視覺結果與比對結果格式化為結構化文字注入 prompt（視覺結果與比對結果以結構化文字注入 prompt）
- [x] 3.3 實作 generate uncle-persona response：呼叫 Claude API，組合 system prompt + few-shot 範例 + 格式化輸入
- [x] 3.4 實作 response generated with cilantro detected：確認香菜情境觸發強烈吐槽回應
- [x] 3.5 實作 response generated with high confidence store match：信心高時用「很像 XX」語氣
- [x] 3.6 實作 response generated with medium confidence store match：信心中等時用「有點像 XX，但不太確定」語氣
- [x] 3.7 實作 response generated with tie result：平手時大叔說「大眾臉，不玩了啦」
- [x] 3.8 實作 response generated with no store match：空 matches 且非平手時說「好像沒吃過，謝謝推薦」
- [x] 3.9 確認 response returned as string：回傳純繁體中文字串，無 JSON 包裝
- [x] 3.10 實作 response length constraint：prompt 指定 50~80 字，設定 max_tokens 保險（回應長度以 prompt 指定 50~80 字，並設 max_tokens 保險）
- [x] 3.11 實作 API failure fallback：API 失敗時回傳大叔風格訊息，不拋出例外（API 失敗回傳大叔風格 fallback，不拋出例外）
- [x] 3.12 實作 non-lu-rou-fan input handling：收到 is_lu_rou_fan: false 時回傳「走錯棚」風格訊息
- [x] 3.13 實作 low confidence photo handling：信心低時大叔吐槽拍照手抖，仍嘗試評論
- [x] 3.14 實作 store familiarity language：照片數量反映大叔熟悉度語氣，而非輸出數字——照片多的店用「很熟」、照片少的用「不常去」語氣

## 4. 內容安全防護（content safety guardrail）

- [x] 4.1 實作 content safety guardrail 內容安全檢查函式：偵測仇恨、侮辱、性愛、暴力、不法行為五類內容（內容安全防護使用 prompt 層規則，保留升級至輸出後檢查的空間）
- [x] 4.2 實作 hate content blocked：仇恨內容觸發時回傳安全 fallback 訊息
- [x] 4.3 實作 insult content blocked：侮辱／霸凌內容觸發時回傳安全 fallback 訊息
- [x] 4.4 實作 sexual content blocked：性愛相關內容觸發時回傳安全 fallback 訊息
- [x] 4.5 實作 violence content blocked：暴力內容觸發時回傳安全 fallback 訊息
- [x] 4.6 實作 illegal activity content blocked：不法行為內容觸發時回傳安全 fallback 訊息
- [x] 4.7 確認 safe response passes through：正常回應不受防護機制影響直接回傳

## 5. 整合測試

- [x] 5.1 以假資料測試：有香菜 + 高信心比對 → 確認吐槽 + 「很像 XX」語氣
- [x] 5.2 以假資料測試：中信心比對 → 確認「有點像，不太確定」語氣
- [x] 5.3 以假資料測試：平手（is_tie: true）→ 確認「大眾臉，不玩了」語氣
- [x] 5.4 以假資料測試：空 matches → 確認「好像沒吃過，謝謝推薦」
- [x] 5.5 測試範例檔不存在時系統正常運作（fallback）
- [x] 5.6 測試安全防護：模擬觸發各類違規內容，確認 fallback 訊息正確回傳
