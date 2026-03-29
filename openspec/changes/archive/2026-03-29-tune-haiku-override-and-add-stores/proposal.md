## Why

Haiku override 觸發閾值過低（0.5），導致碗色等單一特徵即可蓋過 CLIP 結果，造成辨識錯誤（如司機俱樂部被誤判為晴光）。同時新增 5 家店家，並補充視覺特徵詞彙以提升 Haiku 辨識精度。

## What Changes

- 將 Haiku override 閾值從 0.5 提升至 0.75，要求多個特徵同時命中才觸發覆蓋
- 晴光小吃改為需要「綠碗 + 黃蘿蔔」才觸發 override（碗 0.5 + 配料 0.3 = 0.8）
- 司機俱樂部新增 distinctive 綠碗，與晴光同色碗時形成競爭，無配料時交由 CLIP 決定
- 新增 `silver` 碗色與 `metal` 碗質感，支援矮仔財不鏽鋼碗辨識
- 補充 toppings 描述（pickled_radish 強調放在飯上、pickled_cucumber 改名、新增 yin_gua 蔭瓜）
- `toppings.yaml` 新增 `yin_gua`，`cucumber` 改名為 `pickled_cucumber`，縮短描述符合 CLIP 77 token 限制
- 新增 5 家店家：珠記大橋頭油飯、天天利美食坊、一甲子餐飲、司機俱樂部、矮仔財

## Capabilities

### New Capabilities

（無新 spec）

### Modified Capabilities

- `knn-store-matching`：override 閾值預設值從 0.5 改為 0.75；同色碗多店競爭時的平手行為
- `visual-feature-recognizer`：新增 bowl_color（silver）、bowl_texture（metal）；更新 toppings 詞彙（yin_gua、pickled_cucumber）

## Impact

- Affected code:
  - `src/store_matching/matcher.py` — `_HAIKU_OVERRIDE_THRESHOLD` 0.5 → 0.75
  - `eval_hybrid.py` — `_HAIKU_OVERRIDE_THRESHOLD` 0.5 → 0.75
  - `src/visual_recognition/classifier.py` — 新增 silver/metal，更新 toppings 描述
  - `src/visual_recognition/config/toppings.yaml` — 新增 yin_gua，改名 pickled_cucumber
  - `data/store_notes.json` — 新增 5 家店，調整晴光碗設定，新增司機俱樂部碗設定，新增矮仔財銀碗
