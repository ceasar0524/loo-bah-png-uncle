# line-rich-menu Specification

## Purpose

定義 LINE 圖文選單的按鈕配置與對應的回應行為。目前為六格版型，已啟用四個按鈕。

## Requirements

### Requirement: Rich Menu buttons

The Rich Menu SHALL use a six-column layout with the following five active buttons: 怎麼用、店家清單、大叔雷達、隨機驚喜、巷子口.

#### Scenario: User taps 怎麼用

- **WHEN** the user sends the text "怎麼用"
- **THEN** the system SHALL reply with a fixed usage instruction message explaining how to send a photo to get a store identification result

#### Scenario: User taps 店家清單

- **WHEN** the user sends the text "店家清單"
- **THEN** the system SHALL reply with a dynamically generated Flex Message listing all stores in `data/store_notes.json`, grouped by district

#### Scenario: User taps 大叔雷達

- **WHEN** the user sends the text "大叔雷達"
- **THEN** the system SHALL reply with a fixed text message explaining how the radar (nearby store matching) feature works

#### Scenario: User taps 隨機驚喜

- **WHEN** the user sends the text "隨機驚喜"
- **THEN** the system SHALL enter random mode and prompt the user to share their location
- **AND** subsequent location shares SHALL trigger the random nearby store recommendation flow

#### Scenario: User taps 巷子口

- **WHEN** the user sends the text "巷子口"
- **THEN** the system SHALL reply with a Quick Reply message listing available districts from `data/hidden_gems.json`


<!-- @trace
source: hidden-gems-list
updated: 2026-04-14
code:
  - app.py
  - data/hidden_gems.json
-->

---
### Requirement: Store list generation

The store list SHALL be dynamically generated from `store_notes.json` at request time, so it always reflects the current store count without code changes.

#### Scenario: Store list format

- **WHEN** the store list is requested
- **THEN** the system SHALL return a message listing all store names, one per line, prefixed with a bullet, and including the total count


<!-- @trace
source: rich-menu
updated: 2026-04-13
code:
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_10.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_10.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_10.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_6.jpg
  - index_vit_l14.npz
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_3.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_12.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_13.png
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_10.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_6.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_7.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_1.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_3.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_1.png
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_6.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_7.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_1.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_5.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_1.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_10.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_11.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_11.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_2.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_9.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_1.jpeg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_12.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_2.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_10.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_11.jpg
  - haiku_features_cache_v2.json
  - photos_sauce_crop/天天利美食坊（稠）/photo_3.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_1.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_1.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_8.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_13.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_8.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_6.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_10.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_5.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_1.jpg
  - app.py
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_14.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_1.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_2.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_10.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_5.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_10.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_15.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_7.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_11.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_11.jpg
  - index_dino_crop.npz
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_1.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_1.jpeg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_6.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_10.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_5.jpg
  - eval_dino.py
  - photos_sauce_crop/小王煮瓜（水）/photo_7.jpg
-->

---
### Requirement: Rich Menu configuration

The Rich Menu SHALL be configured in LINE Official Account Manager with collapsed state as default, so it does not occupy chat space until the user expands it.

#### Scenario: Default collapsed state

- **WHEN** a user opens the chat
- **THEN** the Rich Menu SHALL be collapsed by default and expandable on tap

<!-- @trace
source: rich-menu
updated: 2026-04-13
code:
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_10.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_10.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_10.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_6.jpg
  - index_vit_l14.npz
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_3.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_12.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_13.png
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_10.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_6.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_7.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_1.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_3.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_1.png
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_6.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_7.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_1.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_5.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_1.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_10.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_11.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_11.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_2.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_9.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_1.jpeg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_12.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_2.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_10.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_11.jpg
  - haiku_features_cache_v2.json
  - photos_sauce_crop/天天利美食坊（稠）/photo_3.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_1.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_1.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_8.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_13.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_8.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_6.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_10.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_5.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_1.jpg
  - app.py
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_14.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_1.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_2.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_10.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_5.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_10.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_15.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_7.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_11.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_11.jpg
  - index_dino_crop.npz
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_1.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_1.jpeg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_6.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_10.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_5.jpg
  - eval_dino.py
  - photos_sauce_crop/小王煮瓜（水）/photo_7.jpg
-->