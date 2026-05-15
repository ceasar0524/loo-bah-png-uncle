## Why

推薦結果只有大叔單方面的說法，缺少真實用戶的聲音。加入用戶代號與評價讓推薦更有說服力——「魯肉飯勇者#12 說這家必吃」比大叔自己說更讓人相信。

## What Changes

- 打卡後新增評價入口：Quick Reply 提供「必吃 👍」/「普通 😐」/「不能只有我吃到 🤫」三個評價選項
- 評價儲存至 Firestore `store_ratings/<store_name>/votes/<user_id>`
- 隨機驚喜、個人化推薦、巷仔口結果中，Flex Message 加入「查看評價 💬」按鈕，點擊開啟 LIFF 頁面
- LIFF 頁面以動態方式（跑馬燈/輪播，實作時決定）顯示該店所有 must_eat 評價代號
- 每個推薦結果加入「分享這家店 📤」按鈕，透過 LIFF shareTargetPicker 發送含店家資訊、Google Maps 連結與用戶稱號代號的分享訊息
- 評價數據影響隨機驚喜推薦權重（高評價店家被抽到的機率加成）

## Capabilities

### New Capabilities

- `store-ratings`: 打卡後評價流程、評價 Firestore 儲存、評價讀取與權重計算
- `ratings-liff`: LIFF 評價展示頁，以動態效果呈現該店 must_eat 評價代號清單
- `share-liff`: LIFF 分享頁，呼叫 shareTargetPicker 發送含店家資訊與用戶稱號代號的分享訊息

### Modified Capabilities

- `random-nearby-recommendation`: 推薦權重加入評價加成，Flex Message 加入用戶代號背書
- `personal-taste-recommendation`: Flex Message 加入用戶代號背書
- `hidden-gems-list`: Flex Message 加入用戶代號背書

## Impact

- Affected specs: `store-ratings`（新增）、`ratings-liff`（新增）、`share-liff`（新增）、`random-nearby-recommendation`（修改）、`personal-taste-recommendation`（修改）、`hidden-gems-list`（修改）
- Affected code: `app.py`、Firestore `store_ratings` collection、新增 `/liff/ratings` 與 `/liff/share` Flask 路由、LINE Developers Console 需設定兩個 LIFF app
