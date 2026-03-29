# 魯肉飯評論器

丟一張魯肉飯照片，讓大叔來評論。

> 此工具為實驗性質，評論僅供參考。每個人口味不一樣，最重要的是找到屬於自己最愛的魯肉飯。

---

## 大叔是誰？

從年輕就愛吃魯肉飯，年輕時夢想吃遍全台好吃的魯肉飯。隨著年紀越大、肚子越大，抱著「現在不吃以後就沒機會」的心態，已完成 30 天吃完 30 家的挑戰，未來目標是挑戰兩百、三百家，吃遍全台灣。

大叔把每碗魯肉飯都當寶，對他來說沒有不好吃的魯肉飯，只有更好吃的魯肉飯。唯二例外是香菜和蔥——那是大叔的罩門，看到就忍不住要碎念幾句。

---

## 怎麼用

1. 加入 LINE Bot
2. 丟一張魯肉飯照片
3. 看大叔怎麼說

加入 LINE Bot，傳照片試試看：

[![加入魯肉飯大叔](assets/line-qr.png)](https://line.me/R/ti/p/%40940srtss)

👉 [https://line.me/R/ti/p/@940srtss](https://line.me/R/ti/p/%40940srtss)

---

## 大叔去過哪些店

| 店名 | 地區 |
|------|------|
| 玉女號魯肉飯 | 林口區 |
| 晴光小吃 | 林口區 |
| 阿興魯肉飯 | 中和區 |
| 明志派出所對面滷肉飯 | 泰山區 |
| 雙胖子 | 大同區 |
| 珠記大橋頭油飯 | 大同區 |
| 滷三塊五花肉飯 | 北投區 |
| 矮仔財滷肉飯 | 北投區 |
| 313號鵝肉擔 | 北投區 |
| 北北車魯肉飯 | 中正區 |
| 黃記魯肉飯 | 中山區 |
| 龍記小吃店 | 中山區 |
| 天天利美食坊 | 萬華區 |
| 一甲子餐飲 | 萬華區 |
| 司機俱樂部 | 松山區 |

持續擴充中。

---

## 技術架構

- **視覺辨識**：Claude Haiku Vision 辨識配料、碗色等特徵
- **店家比對**：CLIP embedding + KNN 向量比對
- **評論生成**：Claude Haiku 扮演大叔，根據辨識結果產生台式風格評論
- **部署**：LINE Bot Webhook + GCP Cloud Run

---

## 判斷邏輯

辨識流程分為兩個階段：

**第一階段：判斷是哪一家店**

1. CLIP 將照片向量化，與資料庫中各店家的照片向量做 KNN 相似度比對，選出最像的店家
2. 同時，Claude Haiku 分析照片中的碗色、碗形、配料等視覺特徵
3. 將 Haiku 偵測結果與 `store_notes.json` 中各店家的 `known_toppings`（已知配料）和 `bowl`（碗型特徵）交叉比對，計算各店家得分
4. 若某家店得分明顯高於其他店，則覆蓋 CLIP 的結果，直接鎖定該店；若多家同分，則退回 CLIP 的判斷

**第二階段：決定說什麼**

1. 根據第一階段確定的店家，從 `store_notes.json` 讀取該店的背景故事與已知配料
2. 將視覺辨識結果、店家背景知識一起傳給 Claude Haiku，由大叔以台灣大叔口吻生成回覆

---

## 開發方式

本專案透過 **Claude Code**（AI 編程助理）與 **Spectra**（Spec-Driven Development 工具）協作完成。由人主導需求與決策，AI 協助實作與規格管理。

規格文件存放於 `openspec/`，每個功能都有對應的 proposal、spec、design 與 tasks。

---

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

### 重建 KNN index

```bash
python build_index.py
```

## 部署

使用 GCP Cloud Run，透過 GitHub Actions 自動部署。每次 push 到 `main` branch 會自動建置 Docker image 並部署。
