## 1. GCP 基礎設定

- [x] 1.1 使用 GCP Cloud Run 作為部署平台：啟用 Cloud Run、Artifact Registry、Cloud Build API（Cloud Run service configuration）
- [x] 1.2 使用 GitHub Actions 做 CI/CD：建立 Artifact Registry Docker repository `loo-bah-png`（Continuous deployment via GitHub Actions）
- [x] 1.3 建立 Service Account `github-actions` 並授予 run.admin、artifactregistry.writer、iam.serviceAccountUser 權限（Continuous deployment via GitHub Actions）
- [x] 1.4 產生 Service Account JSON key 並存入 GitHub Secret `GCP_SA_KEY`（Continuous deployment via GitHub Actions）
- [x] 1.5 將 `ANTHROPIC_API_KEY`、`LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN` 存入 GitHub Secrets（Environment variables available at runtime）

## 2. Docker image build

- [x] 2.1 建立 `Dockerfile`，安裝系統依賴、Python 套件，並預先下載 CLIP 模型（Docker image build）
- [x] 2.2 修正 `requirements.txt`：新增 `pyyaml`，調整 `opencv-python-headless` 至 4.10.0.84 解決 numpy 版本衝突（Docker image build）

## 3. GitHub Actions CI/CD

- [x] 3.1 建立 `.github/workflows/deploy.yml`，實作 push to main 自動 build、push、deploy 流程（Continuous deployment via GitHub Actions）
- [x] 3.2 記憶體設定為 4Gi、cpu=2、使用 --no-cpu-throttling（Cloud Run service configuration）

## 4. 啟動最佳化

- [x] 4.1 啟動時預載 CLIP 模型：在 `app.py` module level 呼叫 `clip_model.get_model()`（CLIP model preloading at startup）
- [x] 4.2 將圖片下載（`get_message_content`）移至 background thread，避免 webhook handler 阻塞（Cloud Run service configuration）

## 5. 驗證

- [x] 5.1 確認 GitHub Actions 跑完後 Cloud Run 服務正常啟動（Container starts successfully）
- [x] 5.2 更新 LINE Developers webhook URL 為 Cloud Run HTTPS endpoint，Verify 通過（Continuous deployment via GitHub Actions）
- [x] 5.3 傳照片測試，確認 Bot 正常回應（First request after cold start does not wait for model load）
