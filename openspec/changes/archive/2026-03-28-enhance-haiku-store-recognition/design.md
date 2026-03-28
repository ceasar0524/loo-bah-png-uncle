## Context

`matcher.py` 的 `haiku_override()` 讀取 `store_notes.json` 的 `bowl` 與 `known_toppings` 欄位，對照 Haiku classifier 偵測結果來計算各店家得分，得分超過門檻且唯一勝出時覆蓋 CLIP KNN 結果。原始資料不完整，多數店家缺乏 `known_toppings` 或 `bowl`，且 classifier 的配料清單缺少 `yin_gua`、`pickled_cucumber`，導致部分店家的特徵無法被偵測。

## Goals / Non-Goals

**Goals:**
- 補齊 10 家店的 `known_toppings`、`bowl`、`notes`
- 新增 `yin_gua`、`pickled_cucumber` 配料類別至 Haiku prompt
- 區分 `pickled_radish`（黃色醃蘿蔔）與 `pickled_cucumber`（深色醬瓜）避免混淆

**Non-Goals:**
- 不修改 `haiku_override()` 的計分邏輯
- 不修改 KNN 比對流程
- 不新增店家

## Decisions

### 白色普通圓碗不標 distinctive

白色圓碗在魯肉飯攤極為普遍，若多家店都標 `distinctive: true`，`haiku_override()` 同分互消，覆蓋被抑制，反而無效。只有外觀罕見的碗（螢光綠、黃色美耐皿）才標 `distinctive`。

### pickled_cucumber 獨立於 pickled_radish

醃蘿蔔（泡菜蘿蔔）與醬瓜（深色脆瓜）外觀、顏色不同，需分開辨識。在 prompt 中加入說明幫助 Haiku 區分。

## Risks / Trade-offs

- **黃色碗誤判風險**：黃色美耐皿在小吃攤不算罕見，明志派出所標 distinctive 可能造成誤判。→ 後續可視測試結果決定是否移除。
- **313鵝肉擔與龍記無特徵**：這兩家無獨特配料也無特色碗，完全依賴 CLIP，辨識準確率受照片數量限制。
