## Why

魯肉飯辨識器的核心體驗不是數據輸出，而是「有靈魂的回應」。本模組實作一位愛吃魯肉飯的台灣大叔 persona，將視覺分析結果與店家比對結果轉化為台式幽默口吻的自然語言回應，包含吐槽、感嘆、文化哏與推薦。

## What Changes

- 新增大叔 persona LLM 模組，接收視覺辨識結果與店家比對結果，透過 Claude API 產出繁體中文回應
- 新增 few-shot 範例管理機制，從外部設定檔載入範例，支援不改程式碼即可調整 persona 風格
- 新增內建預設範例作為 fallback，確保範例檔案缺失時系統仍可正常運作

## Capabilities

### New Capabilities

- `uncle-persona-response`: 大叔 persona LLM 回應生成，整合視覺結果與店家比對，輸出台式幽默文字
- `persona-examples`: few-shot 範例管理，從設定檔載入，支援 fallback 至內建範例

### Modified Capabilities

（無）

## Impact

- 外部依賴：Claude API（`anthropic` Python SDK）
- 新增檔案：`modules/uncle_persona.py`、`examples/uncle_examples.json`
- 輸入介面：接收視覺辨識結果 dict 與店家比對結果 list
- 輸出介面：回傳繁體中文字串
