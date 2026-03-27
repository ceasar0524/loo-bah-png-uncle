## Why

六個模組各自獨立，需要一個統一的命令列入口將它們串接起來，讓使用者只需提供一張照片路徑就能得到完整的魯肉飯辨識結果與大叔回應。

## What Changes

- 新增 `recognize.py` 命令列腳本，接受照片路徑為參數
- 依序執行：image-preprocessing → visual-recognition → store-matching → uncle-persona
- 將 uncle-persona 的回應印出到終端機
- 新增獨立的 `build_index.py` 腳本，用於建立或重建向量索引

## Capabilities

### New Capabilities

- `end-to-end-pipeline`: 整合所有模組的完整辨識流程，從照片輸入到大叔回應輸出
- `index-builder-cli`: 命令列介面，掃描照片目錄、建立向量索引並儲存至磁碟

### Modified Capabilities

(none)

## Impact

- Affected specs: `end-to-end-pipeline`, `index-builder-cli`
- Affected code:
  - `recognize.py`（主程式入口）
  - `build_index.py`（索引建立腳本）
- Depends on: `image-preprocessing`、`visual-recognition`、`store-matching`、`uncle-persona`、`store-embedding-db`
