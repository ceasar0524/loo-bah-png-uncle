## 1. Classifier 配料類別更新

- [x] 1.1 在 classifier.py 的 Haiku prompt 新增 `yin_gua` 至 toppings 清單（Extract visual features in same Haiku call as classification）
- [x] 1.2 在 classifier.py 的 Haiku prompt 新增 `pickled_cucumber` 至 toppings 清單（pickled_cucumber distinguished from pickled_radish）
- [x] 1.3 在 classifier.py 的 Haiku prompt 補充說明，區分 pickled_radish（黃色醃蘿蔔）、pickled_cucumber 獨立於 pickled_radish（深色醬瓜）、cucumber（新鮮黃瓜）（pickled_radish distinguished from pickled_cucumber）

## 2. store_notes.json 資料補充

- [x] 2.1 補充各店家 `known_toppings`：玉女號 soft_boiled_egg、晴光 pickled_radish、阿興 cilantro、雙胖子 yin_gua、滷三塊 pork_floss、北北車 pork_floss、黃記 pickled_cucumber（白色普通圓碗不標 distinctive）
- [x] 2.2 補充各店家 `bowl` 欄位：晴光 bright_green/plastic/distinctive、明志 yellow/plastic/distinctive；移除玉女號、北北車的無效 distinctive 標記（白色普通圓碗不標 distinctive）
- [x] 2.3 更新各店家 `notes` 背景知識：補充雙胖子醬汁描述、313鵝肉擔肉質特色與辣椒醬油、北北車肉鬆說明、滷三塊肉塊大小、龍記肉燥口感
