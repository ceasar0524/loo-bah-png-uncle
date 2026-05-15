## Context

個人化推薦功能透過四題 Quick Reply 問卷收集口味偏好，每次使用都要重填。目前偏好僅存於 in-memory session（`_sessions`），重啟或 TTL 過期後即消失。Firestore 已用於統計功能，可直接擴充使用。

## Goals / Non-Goals

**Goals:**
- 答完問卷後詢問是否儲存偏好至 Firestore
- 已有偏好的用戶可選擇直接用上次偏好或重新填
- 重新填完後再詢問是否更新儲存

**Non-Goals:**
- 提供主動刪除偏好的功能（選「重新填」覆蓋即可）
- 儲存位置偏好（每次仍需分享位置）
- 跨裝置同步（以 LINE user_id 為 key，同帳號即同步）

## Decisions

### Firestore 儲存結構

Collection：`user_preferences`，Document ID：`user_id`

```json
{
  "taste": {
    "fat_ratio": "lean_heavy",
    "skin": "no_skin",
    "sauce_consistency": "水",
    "sauce_taste": "偏鹹"
  },
  "updated_at": "<timestamp>"
}
```

讀寫非同步處理（`threading.Thread`），不阻塞 webhook 回應。

### 儲存詢問時機

每次答完四題都詢問（無論是否已有儲存），Quick Reply：「儲存 ✅」/「不用 ❌」。選完後繼續詢問位置。

### 已有偏好的觸發流程

觸發「個人化」時先查 Firestore（非同步讀取可接受輕微延遲）。若有偏好，顯示摘要並問：「直接用 ✅」/「重新填 🔄」。

偏好摘要格式：「上次偏好：偏瘦・不黏・不稠・偏鹹」

### Session 狀態擴充

新增 `taste_save_pending` key 存放待儲存的答案，等用戶回覆「儲存/不用」後清除。

新增 `taste_loaded` key 標記本次使用已讀取的 Firestore 偏好，供「直接用」流程使用。

### 新關鍵字

- `儲存 ✅`：將 `taste_save_pending` 寫入 Firestore，清除 key，詢問位置
- `不用 ❌`：清除 `taste_save_pending`，詢問位置
- `直接用 ✅`：從 session 取出 `taste_loaded`，設定 `__taste__`，詢問位置
- `重新填 🔄`：清除 `taste_loaded`，從第一題開始填答

## Risks / Trade-offs

- **Firestore 讀取延遲**：觸發「個人化」時需讀 Firestore，可能有 100–300ms 延遲，但 LINE webhook 回應時限為 30 秒，影響可忽略。
- **Session 狀態複雜度增加**：新增多個 key，需確保各分支正確清除，避免殘留狀態。
