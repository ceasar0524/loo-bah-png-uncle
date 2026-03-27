## Context

recognizer-cli 是整個系統的對外入口。本機階段以命令列腳本形式運作，未來 Line Bot 階段可直接呼叫相同的 pipeline 函式，不需要重寫核心邏輯。

## Goals / Non-Goals

**Goals:**

- `recognize.py`：輸入照片路徑，跑完整流程，印出大叔回應
- `build_index.py`：掃描照片目錄，建立向量索引
- 模組間透過 data-schema 定義的 TypedDict 傳遞資料

**Non-Goals:**

- 不提供 web API（Line Bot 階段另外處理）
- 不做批次辨識（一次一張）
- 不提供互動式 REPL

## Decisions

### pipeline 核心邏輯抽成獨立函式，CLI 只負責 I/O

**選擇**：`pipeline.py` 封裝完整流程，`recognize.py` 只做參數解析與印出
**放棄**：所有邏輯寫在 `recognize.py` 一支檔案

**原因**：
- Line Bot 階段可直接 import `pipeline.run(image)` 不需要改核心邏輯
- CLI 和 API 層各自負責自己的 I/O，pipeline 不知道自己被誰呼叫

### visual-recognition 結果若非魯肉飯，仍繼續送 uncle-persona

**選擇**：is_lu_rou_fan: false 時，跳過 store-matching，直接送 uncle-persona 產生「你走錯棚」回應
**放棄**：非魯肉飯直接印錯誤訊息結束

**原因**：
- 大叔的幽默回應是核心體驗，即使辨識失敗也要有趣
- uncle-persona spec 已定義非魯肉飯的回應情境

### 錯誤訊息用中文印出，不拋 Python traceback

**選擇**：捕捉常見錯誤（檔案不存在、API key 未設定），印出友善的中文提示
**放棄**：讓例外直接噴出

**原因**：
- 系統之後會開放給朋友或公開使用，traceback 對一般使用者沒有意義
- 錯誤訊息直接告訴使用者該怎麼做

## Risks / Trade-offs

- **CLIP 模型第一次載入較慢（5–15 秒）** → 屬於預期行為，CLI 可印出「載入模型中...」提示
- **Claude API key 未設定** → 捕捉並印出明確提示：`請設定環境變數 ANTHROPIC_API_KEY`
