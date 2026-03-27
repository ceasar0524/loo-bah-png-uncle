## Why

LINE Bot webhook 需要一個公開的 HTTPS 端點才能接收 LINE 的訊息。本機開發用 ngrok 只能臨時使用，需要一個穩定的雲端部署方案讓 Bot 持續對外服務。

## What Changes

- 新增 `Dockerfile`，打包 Flask app、CLIP 模型與所有依賴
- 新增 GitHub Actions workflow（`.github/workflows/deploy.yml`），push to main 自動 build image 並部署
- GCP Artifact Registry 作為 Docker image 倉庫
- GCP Cloud Run 作為無伺服器容器執行環境，設定 4Gi 記憶體、2 CPU、`--no-cpu-throttling`
- 三個環境變數（`ANTHROPIC_API_KEY`、`LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN`）透過 Cloud Run 注入，不寫進 image
- 啟動時預載 CLIP 模型，避免第一個請求才觸發載入

## Capabilities

### New Capabilities

- `cloud-run-deployment`: 透過 GitHub Actions CI/CD 自動部署到 GCP Cloud Run，提供穩定的 HTTPS webhook 端點

### Modified Capabilities

（none）

## Impact

- 新增檔案：`Dockerfile`、`.github/workflows/deploy.yml`
- 修改：`requirements.txt`（新增 `pyyaml`，調整 opencv 版本至 4.10.0.84）、`app.py`（啟動時預載 CLIP 模型、圖片下載移至 background thread）
- GCP 資源：Cloud Run service `loo-bah-png`、Artifact Registry repository `loo-bah-png`、Service Account `github-actions`
- Cloud Run URL：`https://loo-bah-png-r2jxjg7r4q-de.a.run.app`
