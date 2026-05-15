## Context

足跡打卡（luroufan-footprint）和稱號系統（user-title-system）已建立用戶代號機制。社群感功能以這些代號為基礎，在推薦結果中加入真實用戶的聲音，讓同好的評價直接可見。

## Goals / Non-Goals

**Goals:**
- 打卡確認後提供評價入口（三個選項）
- 評價儲存至 Firestore，每位用戶每家店只計一票
- 推薦 Flex Message 顯示「N 位同好推薦 🔥」小標籤（有 must_eat 票時才顯示）
- 推薦 Flex Message 加入「查看評價 💬」與「分享這家店 📤」兩個按鈕
- LIFF 頁面動態展示該店 must_eat 評價代號（動態風格於實作時決定）
- 分享 LIFF 呼叫 shareTargetPicker，發送含店家資訊、Google Maps 連結與用戶稱號代號的訊息

**Non-Goals:**
- 不做推薦權重加成（改用可見標籤取代隱性加權）
- 不在 Flex Message 靜態顯示代號背書（改用 LIFF 動態展示）
- 不支援刪除或修改評價
- 不做評價排行榜

## Decisions

### 評價選項與語意

三個選項對應不同情緒，刻意不用「好吃/難吃」：

| 按鈕 | 語意 | 儲存值 |
|------|------|--------|
| 必吃 👍 | 強烈推薦 | `must_eat` |
| 普通 😐 | 還好 | `neutral` |
| 不能只有我吃到 🤫 | 太難吃，要拖朋友一起受苦 | `bad` |

「不能只有我吃到」是負面評價——太難吃，不能只有自己吃到。儲存為 `bad`，不計入同好推薦標籤。

### 評價 Firestore 資料結構

```
store_ratings/<store_name>/votes/<user_id>
  rating: "must_eat" | "neutral" | "bad"
  rated_at: timestamp
  title: string（用戶當時的稱號，供背書顯示用）
  title_number: int
```

每位用戶每家店只有一筆記錄（以 user_id 為 document ID），重複評價直接覆蓋。

### LIFF 評價展示頁

推薦 Flex Message 底部加入「查看評價 💬」按鈕（URIAction），點擊開啟 `/liff/ratings?store=<store_name>` LIFF 頁面。

LIFF 頁面從後端 API `/api/ratings/<store_name>` 取得 must_eat 評價代號清單，以動態效果展示。動態風格（跑馬燈/輪播/彈幕）於實作時決定，spec 不限定實作細節。

若無 must_eat 評價，LIFF 頁面顯示「還沒有人評價，你來當第一個！」

LIFF app 需在 LINE Developers Console 手動設定，endpoint 為 Cloud Run 部署的服務 URL。

### 同好推薦標籤

推薦 Flex Message 中，若店家有 `must_eat` 評價，在店名下方顯示小標籤：

`N 位同好推薦 🔥`

其中 N 為該店 `must_eat` 票數。無 `must_eat` 票則不顯示標籤。

標籤適用所有推薦場景：隨機驚喜、附近推薦、個人推薦、巷仔口附近清單。

### 分享 LIFF 頁面

推薦 Flex Message 底部加入「分享這家店 📤」按鈕（URIAction），點擊開啟 `/liff/share?store=<store_name>` LIFF 頁面。

LIFF 頁面取得用戶稱號代號（從 Firestore 讀取或從 URL 參數帶入），立即呼叫 `liff.shareTargetPicker()`，發送一則 Flex Message 包含：
- 店家名稱
- Google Maps 連結
- 用戶稱號代號（如「魯肉飯勇者#12 推薦這家！」）
- bot 加入連結（固定文字）

用戶選完聯絡人後，LIFF 頁面自動關閉回到對話。

### 評價入口時機

評價 Quick Reply 在打卡確認訊息之後送出（不在升級儀式感訊息之後，避免訊息過多）。

若同次打卡同時觸發升級，順序：打卡確認 → 升級儀式感 → 評價邀請。

## Risks / Trade-offs

- **評價資料量少**：初期用戶少，部分店家可能長期無評價 → 無評價時不顯示背書，不強制
- **高稱號用戶主導**：魯肉飯大神的評價比無職轉生者更顯眼 → 這是設計意圖，鼓勵用戶升級
- **Firestore 讀取次數增加**：每次推薦需多讀一次評價資料 → 評價資料量小，影響可忽略

## Open Questions

（無）
