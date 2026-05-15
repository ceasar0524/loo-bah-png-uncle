## Context

個人化口味測驗已可儲存用戶的四個口味維度答案至 Firestore（`taste_preference-persistence` spec）。用戶可透過「查看個人口味設定」觸發查詢。目前回覆只顯示口味偏好文字，缺乏個性化趣味。

本次新增人格台詞功能，根據口味答案對應一句描述性台詞，在查看設定時一起顯示。

## Goals / Non-Goals

**Goals:**
- 新增口味組合 → 人格台詞對應表（hardcoded，7 組）
- 在「查看個人口味設定」回覆中顯示台詞

**Non-Goals:**
- 不新增資料庫欄位（台詞從現有答案即時運算）
- 不在推薦結果頁面顯示台詞（僅在查看設定時顯示）
- 不支援用戶自訂台詞

## Decisions

### 台詞以 hardcoded 字典實作

台詞固定 7 組，不需要從外部資料來源載入。在 `app.py` 中定義 `_PERSONALITY_TAGLINES` 字典，key 為口味組合 tuple，value 為台詞字串。

`get_personality_tagline(answers)` 函式依優先規則查找：
1. 偏甜 → 南部甜心台詞
2. 全都可以 → 通吃者台詞
3. 精確 tuple 匹配 → 對應台詞
4. fallback → 通吃者台詞

answers 結構沿用現有 taste_quiz 的儲存格式：`fat_ratio`, `skin`, `sauce_consistency`, `sauce_taste`

### 顯示位置

在「查看個人口味設定」的文字回覆訊息中，於口味偏好摘要後新增一行台詞，以引號或特別格式標示。

## Risks / Trade-offs

- 部分口味組合（如 偏瘦/with_skin）目前無對應台詞 → fallback 到通吃者，行為合理
- 台詞 hardcoded，未來修改需改 code → 可接受，台詞更新頻率極低
