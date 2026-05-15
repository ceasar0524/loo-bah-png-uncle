## 1. 台詞對應表實作

- [x] 1.1 在 app.py 中新增 `_PERSONALITY_TAGLINES` 字典（台詞以 hardcoded 字典實作），涵蓋 7 組口味組合 → 台詞的對應
- [x] 1.2 實作 `get_personality_tagline(answers)` 函式，依優先規則進行 personality tagline mapping：偏甜優先、全都可以、精確 tuple 匹配、fallback 通吃者

## 2. 顯示整合

- [x] 2.1 在「查看個人口味設定」的回覆邏輯中，加入 display personality tagline in taste settings：取得 Firestore 儲存的答案後呼叫 `get_personality_tagline`，依顯示位置設計決策將台詞附加在口味摘要後方顯示
- [x] 2.2 確認用戶無儲存偏好時不顯示台詞（符合 user has no saved preferences 情境）
