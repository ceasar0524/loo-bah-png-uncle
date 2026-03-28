## Why

現有的 Haiku 特徵辨識缺乏完整的店家配料與碗型資料，導致 Haiku override 機制無法有效區分各店家。透過補充 `store_notes.json` 的 `known_toppings`、`bowl` 欄位與 `notes` 背景知識，並在 classifier 新增 `yin_gua`、`pickled_cucumber` 配料類別，提升辨識準確率與大叔回覆品質。

## What Changes

- `data/store_notes.json`：為全部 10 家店補充 `known_toppings`（已知配料）、`bowl`（碗型特徵）、`notes`（背景知識）
- `src/visual_recognition/classifier.py`：Haiku prompt 新增 `yin_gua`（Oriental pickling melon）與 `pickled_cucumber`（深色醬瓜）兩個配料類別，並加上說明區分 `pickled_radish`（黃色醃蘿蔔）與 `pickled_cucumber`（深色醬瓜）
- 移除無效的 `bowl.distinctive` 標記（白色普通圓碗不具辨識價值）

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `lu-rou-fan-classifier`：新增 `yin_gua`、`pickled_cucumber` 配料類別；補充 prompt 說明以區分醃漬蔬菜種類

## Impact

- Affected specs: `lu-rou-fan-classifier`
- Affected code: `src/visual_recognition/classifier.py`, `data/store_notes.json`
