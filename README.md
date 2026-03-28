# 魯肉飯大叔

2019 年在 IT 邦幫忙鐵人挑戰賽時，完成了 [30 天 30 碗平民魯肉飯完食 🍚](https://ithelp.ithome.com.tw/users/20120094/ironman/2296)

最近把當時拍的這些照片做成一個小工具：丟一張魯肉飯照片給它，它就會開始評論這碗的風格與特色，用「台灣大叔」口吻吐槽與推薦 😆

目前收錄 10 家店，準確率還在優化中（魯肉飯都長太像了 XD），但已經可以玩玩看！

**目前收錄店家（2026/3/28）：** 
313號鵝肉擔（北投區）、北北車魯肉飯（中正區）、玉女號魯肉飯（林口區）、明志派出所對面滷肉飯（泰山區）、阿興魯肉飯（中和區）、晴光小吃（林口區）、黃記魯肉飯（中山區）、滷三塊五花肉飯（北投區）、龍記小吃店（中山區）、雙胖子（大同區）

---

## Demo

加入 LINE Bot，傳照片試試看：

[![加入魯肉飯大叔](assets/line-qr.png)](https://line.me/R/ti/p/%40940srtss)

👉 [https://line.me/R/ti/p/@940srtss](https://line.me/R/ti/p/%40940srtss)

---

## 功能

- 辨識照片是否為魯肉飯
- 分析視覺特徵（肉型、醬汁、配料等）
- KNN 比對資料庫中的店家
- 以大叔口吻回覆品評

## 判斷邏輯

辨識流程分為兩個階段：

**第一階段：判斷是哪一家店**

1. CLIP 將照片向量化，與資料庫中各店家的照片向量做 KNN 相似度比對，選出最像的店家
2. 同時，Claude Haiku 分析照片中的碗色、碗形、配料等視覺特徵
3. 將 Haiku 偵測結果與 `store_notes.json` 中各店家的 `known_toppings`（已知配料）和 `bowl`（碗型特徵）交叉比對，計算各店家得分
4. 若某家店得分明顯高於其他店（例如偵測到香菜，而只有阿興才有香菜），則覆蓋 CLIP 的結果，直接鎖定該店；若多家同分，則退回 CLIP 的判斷

**第二階段：決定說什麼**

1. 根據第一階段確定的店家，從 `store_notes.json` 讀取該店的 `notes`（背景故事）與 `known_toppings`
2. 過濾 Haiku 偵測到的配料——只保留 `known_toppings` 中有記錄的，避免大叔亂說這家沒有的配料
3. 將視覺辨識結果、店家背景知識一起傳給 Claude Haiku，由大叔以台灣大叔口吻生成回覆

**`store_notes.json` 的角色**

`store_notes.json` 兩個階段都會用到，不同欄位在不同階段發揮作用：

| 欄位 | 用於第一階段 | 用於第二階段 |
|------|------------|------------|
| `known_toppings` | ✓ Haiku override 比對依據 | ✓ 配料過濾 |
| `bowl` | ✓ Haiku override 比對依據 | — |
| `notes` | — | ✓ 大叔回覆的背景知識 |

## 系統架構

```
LINE Bot (使用者傳照片)
        ↓
Flask Webhook (app.py)
        ↓
Pipeline (src/pipeline.py)
    ├── 圖片前處理 (preprocessing.py)
    ├── 視覺辨識 (visual_recognition/)
    │       ├── CLIP 圖片向量化
    │       ├── Claude Haiku 分類器（是否為魯肉飯 + 配料辨識）
    │       └── CLIP 特徵辨識（肉型、醬汁、米飯風格）
    ├── 店家比對 (store_matching/)
    │       ├── KNN 向量相似度比對 (index.npz)
    │       └── Haiku 特徵覆蓋（store_notes.json）
    └── 大叔回覆生成 (uncle_persona/)
            └── Claude Haiku + System Prompt + 店家背景知識
        ↓
LINE Bot 回覆訊息
```

## 使用工具

| 工具 | 用途 |
|------|------|
| [CLIP](https://github.com/openai/CLIP) | 圖片向量化與特徵辨識 |
| [Claude Haiku](https://www.anthropic.com) | 魯肉飯分類、大叔回覆生成 |
| [LINE Messaging API](https://developers.line.biz) | Bot 入口 |
| [Flask](https://flask.palletsprojects.com) | Webhook server |
| [GCP Cloud Run](https://cloud.google.com/run) | 無伺服器部署 |
| [GitHub Actions](https://github.com/features/actions) | CI/CD 自動部署 |

## 開發方式

本專案透過 **Claude Code**（AI 編程助理）與 **Spectra**（Spec-Driven Development 工具）協作完成。由人主導需求與決策，AI 協助實作與規格管理。

規格文件存放於 `openspec/`，每個功能都有對應的 proposal、spec、design 與 tasks。

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
