# 魯肉飯大叔

傳一張魯肉飯照片給 LINE Bot，30 年老饕大叔幫你品評這碗飯。

## 功能

- 辨識照片是否為魯肉飯
- 分析視覺特徵（肉型、醬汁、配料等）
- KNN 比對資料庫中的店家
- 以大叔口吻回覆品評

## 本機執行

### 環境需求

- Python 3.11
- 參考 `requirements.txt` 安裝依賴

```bash
pip install -r requirements.txt
```

### 環境變數

建立 `.env` 並填入以下變數（不要 commit 此檔案）：

```
ANTHROPIC_API_KEY=...
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

### 單張圖片辨識（CLI）

```bash
python recognize.py <圖片路徑>
```

### 啟動 LINE Bot webhook server

```bash
python app.py
```

預設在 `0.0.0.0:8080` 啟動。本機測試可搭配 ngrok 暴露 HTTPS endpoint。

### 重建 KNN index

```bash
python build_index.py
```

會讀取 `photos/` 目錄下的店家照片，產生 `index.npz`。

## 部署

使用 GCP Cloud Run，透過 GitHub Actions 自動部署。

每次 push 到 `main` branch 會自動：
1. 建置 Docker image
2. 推送到 GCP Artifact Registry
3. 部署到 Cloud Run

### 所需 GitHub Secrets

| Secret | 說明 |
|--------|------|
| `GCP_SA_KEY` | GCP Service Account JSON key（base64 編碼） |
| `ANTHROPIC_API_KEY` | Anthropic API 金鑰 |
| `LINE_CHANNEL_SECRET` | LINE Messaging API Channel Secret |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API Channel Access Token |

## 專案結構

```
src/
  pipeline.py            # 核心流程
  visual_recognition/    # CLIP 圖片辨識
  store_matching/        # KNN 店家比對
  uncle_persona/         # 大叔回覆生成
  preprocessing.py       # 圖片前處理
data/
  store_notes.json       # 各店家筆記與視覺特徵
photos/                  # 店家照片（不進 git）
openspec/                # Spectra SDD 規格文件
```
