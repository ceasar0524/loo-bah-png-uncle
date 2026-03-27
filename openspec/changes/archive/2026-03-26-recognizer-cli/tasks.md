## 1. Pipeline 核心

- [x] 1.1 建立 `src/pipeline.py`，實作「pipeline 核心邏輯抽成獨立函式，CLI 只負責 I/O」：封裝 image-preprocessing → visual-recognition → store-matching → uncle-persona 完整流程
- [x] 1.2 實作 end-to-end pipeline from image to uncle-persona response：pipeline 函式接受圖片路徑，回傳大叔回應字串
- [x] 1.3 實作 non-lu-rou-fan image skips store-matching，visual-recognition 結果若非魯肉飯，仍繼續送 uncle-persona：is_lu_rou_fan: false 時跳過 store-matching，直接送 uncle-persona 產生「走錯棚」回應
- [x] 1.4 確認 pipeline function importable by other modules：pipeline.py 可被 import 直接呼叫，不依賴 CLI 環境

## 2. recognize.py CLI

- [x] 2.1 建立 `recognize.py`，實作 CLI entry point accepts image path argument：接受單一照片路徑參數
- [x] 2.2 實作 response printed to stdout：大叔回應印出到終端機
- [x] 2.3 實作 model loading progress indicated：CLIP 載入時印出「載入模型中...」
- [x] 2.4 實作 missing file handled gracefully：檔案不存在時印出友善中文錯誤訊息並以非零碼結束
- [x] 2.5 實作 missing API key handled gracefully：ANTHROPIC_API_KEY 未設定時印出明確中文提示並結束
- [x] 2.6 實作「錯誤訊息用中文印出，不拋 Python traceback」：捕捉常見例外，統一用中文訊息呈現

## 3. build_index.py CLI

- [x] 3.1 建立 `build_index.py`，實作 index builder CLI accepts photos directory argument：接受 `--photos` 與 `--output` 參數
- [x] 3.2 實作 index built from directory argument：呼叫 store-embedding-db 建立索引並儲存
- [x] 3.3 實作 build summary printed on completion：完成後印出店家數與照片總數
- [x] 3.4 實作 missing directory handled gracefully：目錄不存在時印出友善中文錯誤訊息並結束

## 4. 整合測試

- [x] 4.1 用一張魯肉飯照片跑完整流程，確認輸出大叔回應
- [x] 4.2 用一張非魯肉飯照片確認跳過 store-matching 並輸出「走錯棚」回應
- [x] 4.3 測試各種錯誤情境（檔案不存在、API key 未設定）的中文錯誤訊息
