## 1. 更新 system prompt 信心等級語氣規則

- [x] 1.1 修改 `persona.py` system prompt 中 medium 信心的語氣指示：改為「走 XX 那種路線」風格比較語氣，不再猜店名（Store confidence language）
- [x] 1.2 修改 `persona.py` system prompt 中 low 信心 / 無比對的語氣指示：改為描述視覺風格特徵，不提店名（Store confidence language）
- [x] 1.3 確認 high 信心與 Haiku override 的語氣指示不受影響（Store confidence language）

## 2. 驗證

- [x] 2.1 用 medium 信心的輸入跑 `recognize.py`，確認回應不出現直接猜店名的語句
- [x] 2.2 用 low 信心 / 無比對的輸入跑 `recognize.py`，確認回應描述視覺風格而非猜店名
