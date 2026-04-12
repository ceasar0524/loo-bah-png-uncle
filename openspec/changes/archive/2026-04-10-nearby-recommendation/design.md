## Context

目前 LINE Bot 的流程是單向的：用戶傳照片 → 大叔回應辨識結果，結束。本功能在回應後新增一個 Quick Reply 按鈕，讓用戶可選擇性地觸發「附近類似店家搜尋」。

現有架構：
- `app.py`：LINE Bot webhook 入口，處理圖片訊息
- `src/store_matching/matcher.py`：CLIP KNN 比對
- `src/uncle_persona/persona.py`：大叔回應生成
- `data/store_notes.json`：店家資料（目前無經緯度）
- `index.npz`：CLIP 向量索引

## Goals / Non-Goals

**Goals:**
- 辨識完成後顯示「找附近類似的 📍」Quick Reply 按鈕
- 用戶點按鈕後請求分享位置
- 收到位置後搜尋風格相近且距離範圍內的店家
- 大叔 in-character 回應推薦結果
- 不影響現有辨識流程

**Non-Goals:**
- 不做個人喜好記錄
- 不做跨用戶的社群推薦
- 不整合 Google Maps 等外部服務

## Decisions

### 用 visual_profile 比對做風格搜尋

辨識出店家後，取該店的 `visual_profile`（fat_ratio、skin、sauce_color、rice_quality）與所有其他店家比對，計算相符欄位數 / 4 作為相似度分數，取分數最高的前 N 家（排除距離過遠的）。

不使用 CLIP 向量做推薦比對，因為 visual_profile 直接對應口味方向（肥瘦、有無皮、醬色、飯質），推薦結果與實際口感更相符，且零 API 費用、邏輯可解釋。

膠質感（黏嘴感）透過 `with_skin + fat_heavy + dark/black_gold` 組合間接涵蓋，不另加欄位。`texture` 欄位保留給日後個人推薦功能。

半熟荷包蛋（`topping_names.egg == "半熟荷包蛋"`）視為招牌風格特徵，而非一般加點選項。當辨識店家與候選店家同為荷包蛋風格時，相似度加 0.2 分，使排序優先呈現同風格店家。

### 距離計算用 Haversine 公式

店家座標存於 `store_notes.json`（新增 `location.lat`、`location.lng` 欄位），用 Haversine 公式計算用戶與各店家的直線距離，不呼叫外部地圖 API，零費用。

預設搜尋半徑：3 公里（可調整）。

### Session 狀態用 in-memory dict 暫存查詢向量

用戶點 Quick Reply 按鈕後到分享位置之間，需要保存原始查詢向量。用 `{user_id: query_vector}` 的 in-memory dict 暫存，TTL 5 分鐘後自動清除。

Cloud Run 是 stateless，重啟後暫存消失。這在低流量下可接受——用戶若遇到 session 遺失，重傳照片即可。

### 回應附 Google Maps 靜態連結

每家推薦店家附上 `https://maps.google.com/?q=<lat>,<lng>` 連結，讓用戶點擊直接導航。此為靜態 URL，不呼叫任何外部 API，零費用，與「不整合 Google Maps 等外部服務」的 Non-Goal 無衝突。

### Quick Reply 按鈕只在辨識成功時顯示

當 `is_lu_rou_fan=True` 且有 matches 時才附按鈕，避免非魯肉飯或無結果時出現無意義的按鈕。

### 功能開關用環境變數控制

在 `app.py` 讀取環境變數 `NEARBY_SEARCH_ENABLED`（預設 `true`）。設為 `false` 時不顯示 Quick Reply 按鈕，附近推薦功能完全關閉，現有辨識流程不受影響。

需要關閉時直接在 Cloud Run 修改環境變數並重部署，無需改程式碼或回滾版本。修復後改回 `true` 即可重新啟用。

## Risks / Trade-offs

- [風險] Cloud Run 重啟導致 session 遺失 → 用戶重傳照片即可，不影響核心功能
- [風險] 店家座標需手動填入（22 家）→ 一次性工作，資料量小
- [取捨] 用直線距離而非路徑距離 → 誤差在 3 公里範圍內可接受，省去地圖 API 費用
