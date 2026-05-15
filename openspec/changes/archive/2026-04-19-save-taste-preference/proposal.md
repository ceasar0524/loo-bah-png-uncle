## Why

用戶每次使用個人化推薦都要重複填答四題口味問卷，流程繁瑣。提供選擇性儲存偏好的功能，下次可直接使用上次的設定。

## What Changes

- 四題問卷答完後，詢問用戶是否儲存偏好（每次都問）
- 已有儲存偏好的用戶觸發「個人化」時，可選擇直接用上次偏好或重新填答
- 選「重新填」答完後再詢問是否更新儲存
- 偏好以 user_id 為 key 儲存於 Firestore

## Capabilities

### New Capabilities

- `taste-preference-persistence`: 將用戶口味偏好持久化儲存至 Firestore，並在下次使用時提供直接套用的選項

### Modified Capabilities

- `line-bot-webhook`: 修改「個人化」觸發流程，加入偏好儲存詢問與已儲存偏好的快速套用邏輯

## Impact

- 影響檔案：`app.py`
- 依賴：Firestore（已啟用），新增 `user_preferences` collection
- 新增 Quick Reply 選項：「儲存 ✅」/「不用 ❌」/「直接用 ✅」/「重新填 🔄」
