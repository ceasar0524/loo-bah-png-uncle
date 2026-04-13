## Why

用戶加入 LINE Bot 後，不知道怎麼使用，也不清楚收錄了哪些店家。目前只能靠加好友歡迎訊息說明，缺乏隨時可查的固定入口。圖文選單（Rich Menu）可以讓用戶在對話框底部隨時展開，查看使用說明和店家清單，不佔日常聊天版面（預設收起）。

## What Changes

新增 LINE 圖文選單，預設收起，提供兩個固定功能入口：
- **怎麼用**：說明如何使用大叔辨識魯肉飯
- **店家清單**：列出目前收錄的所有店家

## Capabilities

### New Capabilities

- `line-rich-menu`: LINE 圖文選單，預設收起，含怎麼用與店家清單兩個按鈕

### Modified Capabilities

(none)

## Impact

- Affected specs: line-rich-menu（新建）
- Affected code:
  - app.py（可能需要初始化 Rich Menu 或處理按鈕觸發的文字事件）
  - LINE Official Account Manager 後台設定（圖文選單設計與綁定）
