## Why

稱號系統目前只是身份標籤，沒有實際功能差異。為了讓升等有誘因、讓高等級用戶感受到實質獎勵，每個稱號等級解鎖一個專屬技能，強化「RPG 角色成長」的遊戲感。

## What Changes

- 新增 Lv.1 技能「肉盾」：輸入「肉盾」，依口味偏好判斷店家是否適合（🟢適合衝／🟡可試／🔴踩雷）
- 新增 Lv.2 技能「絕對滷域」：足跡頁面解鎖地圖模式，顯示打卡據點與勢力範圍
- 新增 Lv.3 技能「魯拉（ルラ）」：輸入「魯拉」，召喚打卡過的店並一鍵開啟 Google Maps 導航
- 新增 Lv.4 技能「滷界敕令」：大神可輸入「號令」發布每日推薦，所有用戶可在巷子口查看大神推薦牆
- 升級 Flex Message 新增技能解鎖說明
- 新增技能封印訊息：等級不足時回覆「🔒 技能尚未解鎖」，顯示目前稱號與距離解鎖所需家數

## Capabilities

### New Capabilities

- `title-skill-meat-shield`: Lv.1 肉汁騎士技能「肉盾」，依口味偏好判斷店家適合度
- `title-skill-absolute-domain`: Lv.2 滷鍋守護者技能「絕對滷域」，LIFF 地圖顯示打卡據點與光暈範圍
- `title-skill-lura`: Lv.3 魯肉飯勇者技能「魯拉」，召喚打卡記錄並開啟導航
- `title-skill-decree`: Lv.4 魯肉飯大神技能「滷界敕令」，發布推薦與大神推薦牆
- `title-skill-lock-message`: 技能等級不足時的封印訊息，顯示目前稱號與解鎖所需家數

### Modified Capabilities

- `user-title-system`: 升級 Flex Message 新增技能解鎖台詞；稱號等級與技能權限綁定
- `luroufan-footprint`: 足跡頁面新增「絕對滷域」按鈕（Lv.2+ 解鎖）
- `line-bot-webhook`: 新增「肉盾」「魯拉」「號令」文字觸發器與對應處理邏輯

## Impact

- Affected specs: `title-skill-meat-shield`（新）、`title-skill-absolute-domain`（新）、`title-skill-lura`（新）、`title-skill-decree`（新）、`user-title-system`（改）、`luroufan-footprint`（改）、`line-bot-webhook`（改）
- Affected code: `app.py`（主要邏輯）、新增 LIFF 頁面（絕對滷域地圖）、`data/hidden_gems.json`（可選，新增店家口味資料補全）
