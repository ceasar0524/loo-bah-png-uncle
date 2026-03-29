## 1. 調整 Haiku override 閾值與競爭邏輯

- [x] 1.1 將 `src/store_matching/matcher.py` 的 `_HAIKU_OVERRIDE_THRESHOLD` 從 0.5 改為 0.75（閾值從 0.5 提升至 0.75）
- [x] 1.2 將 `eval_hybrid.py` 的 `_HAIKU_OVERRIDE_THRESHOLD` 從 0.5 改為 0.75
- [x] 1.3 在 `data/store_notes.json` 中，晴光小吃的 bowl 改為只保留 `color: bright_green, distinctive: true`（移除 shape/texture），讓碗色單獨不達 0.75 閾值（Haiku feature override for high-confidence distinctive features）
- [x] 1.4 在 `data/store_notes.json` 中，新增司機俱樂部的 distinctive 綠碗（bowl: color bright_green, distinctive: true），建立同色碗競爭（司機俱樂部加入 distinctive 綠碗）

## 2. 視覺特徵詞彙擴充

- [x] 2.1 在 `src/visual_recognition/classifier.py` 中新增 `silver` bowl_color 與 `metal` bowl_texture（detect toppings using binary CLIP classification）
- [x] 2.2 更新 `classifier.py` 的 toppings 說明：pickled_radish 加上「placed directly on top of the rice」（pickled_radish not reported from table background）
- [x] 2.3 在 `src/visual_recognition/config/toppings.yaml` 新增 `yin_gua`，將 `cucumber` 改名為 `pickled_cucumber`，縮短描述符合 CLIP 77 token 限制

## 3. 新增店家資料

- [x] 3.1 在 `data/store_notes.json` 新增珠記大橋頭油飯（大同區）
- [x] 3.2 在 `data/store_notes.json` 新增天天利美食坊（萬華區），`known_toppings: [soft_boiled_egg]`
- [x] 3.3 在 `data/store_notes.json` 新增一甲子餐飲（萬華區），`known_toppings: [pickled_cucumber]`
- [x] 3.4 在 `data/store_notes.json` 新增司機俱樂部（松山區）
- [x] 3.5 在 `data/store_notes.json` 新增矮仔財滷肉飯（北投區），distinctive silver metal bowl

## 4. 驗證

- [x] 4.1 以 `venv/bin/python3 eval_hybrid.py` 執行 leave-one-out 評估，確認整體 hybrid 辨識率與各店數字（leave-one-out evaluation）
- [x] 4.2 確認晴光辨識率 ≥ 75%、司機俱樂部結果可接受
