## Why

完成個人化口味測驗後，用戶只能看到自己的口味偏好設定，缺乏趣味性與記憶點。加入魯肉飯人格台詞，讓每個口味組合有對應的一句話描述，在「查看個人口味設定」時顯示，增加互動樂趣並強化用戶對自身口味的認同感。

## What Changes

- 新增口味組合 → 人格台詞的對應邏輯（7種組合，含「都可以」）
- 「查看個人口味設定」回覆訊息加入人格台詞顯示

## Capabilities

### New Capabilities

- `luroufan-personality-tagline`: 根據用戶的四題口味測驗答案，對應出一句魯肉飯人格台詞，並在查看口味設定時顯示

### Modified Capabilities

- `personal-taste-recommendation`: 查看個人口味設定的回覆訊息新增人格台詞欄位

## Impact

- Affected specs: `personal-taste-recommendation`（delta spec）、新增 `luroufan-personality-tagline`
- Affected code: `app.py`
