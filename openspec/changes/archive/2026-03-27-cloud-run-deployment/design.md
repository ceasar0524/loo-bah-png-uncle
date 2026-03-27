## Context

系統已有 LINE Bot webhook 入口（`app.py`）和完整 pipeline，需要一個穩定的對外 HTTPS 端點。本機 ngrok 方案不適合長期使用，因為每次重啟 URL 會變動。

## Goals / Non-Goals

**Goals:**

- 提供穩定的 HTTPS webhook 端點供 LINE Messaging API 使用
- Push to main 自動觸發部署，不需手動操作
- 敏感金鑰不寫進 image，透過環境變數注入
- Cold start 後第一個請求不需等待模型載入

**Non-Goals:**

- GPU 加速（Cloud Run 不支援 GPU，CLIP 跑 CPU）
- 高可用性或多 region 部署
- 正式的 secret management（暫用環境變數，未來可改 Secret Manager）

## Decisions

### 使用 GCP Cloud Run 作為部署平台

採用 Cloud Run 無伺服器容器平台。有免費額度、支援 HTTPS、自動 scale，對低流量 LINE Bot 最合適。不需管理 VM 或 Kubernetes。

### 使用 GitHub Actions 做 CI/CD

每次 push to main 自動 build Docker image、push 到 Artifact Registry、部署到 Cloud Run。採用 `google-github-actions/auth` + Service Account JSON key 做 GCP 認證。

### 記憶體設定為 4Gi

CLIP 模型啟動時預載需要約 2.2 GiB 記憶體。設定 4Gi 確保啟動和推論都有足夠空間。

### 啟動時預載 CLIP 模型

`app.py` 在 module level 呼叫 `clip_model.get_model()`，讓模型在 container 啟動時就載入完成。避免第一個請求才觸發載入造成額外延遲。

### 使用 --no-cpu-throttling

Cloud Run 預設在 request 結束後節流 CPU，導致 background thread 跑不下去。加上此 flag 讓 CPU 在 request 結束後仍可運作，背景執行緒才能完成 pipeline 處理和回覆。

## Risks / Trade-offs

- **Cold start 延遲** → 目前接受，低流量 Bot 不值得加 min-instances 常駐
- **CPU-only 推論** → CLIP 在 CPU 上推論較慢，但對單次查詢已足夠
- **--no-cpu-throttling 費用** → 請求結束後仍計費至背景執行緒完成，影響有限
- **環境變數注入 token** → 有換行風險，未來可改用 Secret Manager 避免
