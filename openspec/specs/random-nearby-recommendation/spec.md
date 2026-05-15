# random-nearby-recommendation Specification

## Purpose

提供隨機驚喜功能：使用者分享位置後，系統從附近店家中隨機推薦一家，避免重複推薦，並在附近店家抽完後逐步擴大搜尋範圍。

## Requirements

### Requirement: Random nearby store recommendation

The system SHALL accept a user location (latitude, longitude) and return one randomly selected store using a two-tier radius expansion: 3 km → 7 km.

The selected store SHALL include `store_name` and `distance_km`.

Already-recommended stores (tracked in `seen`) SHALL be excluded from each draw within the same session.

#### Scenario: Stores found within 3 km

- **WHEN** a user location is provided and at least one unseen store exists within 3 km
- **THEN** the system SHALL randomly select one store from within 3 km

#### Scenario: 3 km exhausted — prompt user to expand

- **WHEN** all stores within 3 km have been seen
- **THEN** the system SHALL reply with a prompt message and set `expanded = True` in the session
- **AND** the system SHALL NOT auto-reset or auto-pick; the user must press the button again to continue

#### Scenario: Expanded mode — stores in 7 km

- **WHEN** `expanded = True` and the user shares location again
- **THEN** the system SHALL randomly select one store from the 3–7 km range (still excluding seen stores)

#### Scenario: 7 km exhausted, session has seen 10+ stores — easter egg

- **WHEN** all stores within 7 km have been seen AND `len(seen) >= 10`
- **THEN** the system SHALL reset `seen` and reply with the exhausted easter egg Flex Message
- The easter egg SHALL display store name as "自己家", a playful Taiwanese phrase as the tagline, and a disabled map button

#### Scenario: 7 km exhausted, session has seen fewer than 10 stores — silent reset

- **WHEN** all stores within 7 km have been seen AND `len(seen) < 10`
- **THEN** the system SHALL silently reset `seen` and draw again from the flat pool

#### Scenario: Random selection is uniform (flat pool)

- **WHEN** drawing a store for recommendation
- **THEN** the system SHALL use `primary_radius_km = extended_km` so all stores within range have equal probability regardless of distance tier

---
### Requirement: Opening hours filtering

The system SHALL filter the store pool to currently open stores before each draw, based on data in `store_hours.json` (fetched from Google Places API).

Stores with no hours data in `store_hours.json` SHALL be included in every draw regardless of time.

The current time SHALL be evaluated in Asia/Taipei timezone.

#### Scenario: All nearby stores are closed

- **WHEN** no stores in the filtered open pool exist within the current search radius
- **AND** stores do exist within range in the full pool (i.e., it's not a coverage gap)
- **THEN** the system SHALL reply: "這時間大叔看了一圈，附近店家都已打烊了！"

#### Scenario: Some nearby stores are open

- **WHEN** at least one open store exists within range
- **THEN** the system SHALL draw only from open stores

---
### Requirement: Store pool includes hidden gems

The random recommendation pool SHALL include stores from both `store_notes` (24 stores with full metadata) and `hidden_gems` (巷仔口 stores with location only).

Stores present in both sources SHALL be deduplicated, with `store_notes` data taking precedence.

Stores in `hidden_gems` that are the same physical location but have a different name from a `store_notes` entry SHALL be manually excluded via `_HIDDEN_GEMS_RANDOM_EXCLUDE`.

The feature can be toggled via `_HIDDEN_GEMS_IN_RANDOM` flag (default: `True`).


<!-- @trace
source: random-surprise
updated: 2026-04-13
code:
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_10.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_2.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_3.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_7.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_1.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_6.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_13.jpg
  - src/nearby_search/__init__.py
  - index_dino_crop.npz
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_10.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_10.jpg
  - haiku_features_cache_v2.json
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_1.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_10.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_11.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_12.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_13.png
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_12.jpg
  - src/uncle_persona/persona.py
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_8.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_10.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_1.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_2.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_15.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_1.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_5.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_10.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_6.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_10.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_6.jpg
  - eval_dino.py
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_2.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_6.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_7.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_3.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_6.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_5.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_1.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_8.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_1.jpeg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_10.jpg
  - src/nearby_search/searcher.py
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_7.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_9.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_1.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_11.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_1.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_11.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_1.png
  - index_vit_l14.npz
  - photos_sauce_crop/天天利美食坊（稠）/photo_5.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_3.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_11.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_7.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_1.jpeg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_10.jpg
  - app.py
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_11.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_14.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_1.jpg
-->

---
### Requirement: Random recommendation response format

The uncle persona SHALL generate a response for the random nearby recommendation using `generate_random`, referencing the store's style attributes from `store_notes` (fat_ratio, skin, sauce_color, sauce_taste).

The `random_tagline` (籤詩文字) for the recommended store SHALL be fetched from `_random_pool`, which covers both `store_notes` and `hidden_gems` stores.

#### Scenario: Store has style data

- **WHEN** the randomly selected store has `visual_profile` entries in `store_notes`
- **THEN** the response SHALL include a brief style description (e.g., 偏肥、帶皮、醬汁深色)

#### Scenario: Store has no style data

- **WHEN** the randomly selected store has no `visual_profile` in `store_notes`
- **THEN** the response SHALL omit style details and return a location-only recommendation

#### Scenario: Store has random_tagline

- **WHEN** the randomly selected store has a `random_tagline` field in `_random_pool`
- **AND** the recommendation is not a far-distance phrase (far_phrase is falsy)
- **THEN** the system SHALL include the tagline text in the Flex Message response

<!-- @trace
source: random-surprise
updated: 2026-04-13
code:
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_10.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_2.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_3.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_7.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_1.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_6.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_13.jpg
  - src/nearby_search/__init__.py
  - index_dino_crop.npz
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_10.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_10.jpg
  - haiku_features_cache_v2.json
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_1.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_10.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_11.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_12.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_13.png
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_12.jpg
  - src/uncle_persona/persona.py
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_8.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_10.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_1.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_2.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_15.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_1.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_5.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_10.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_6.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_10.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_6.jpg
  - eval_dino.py
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_2.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_6.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_7.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_3.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_6.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_5.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_1.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_8.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_1.jpeg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_10.jpg
  - src/nearby_search/searcher.py
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_7.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_9.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_1.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_11.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_1.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_11.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_1.png
  - index_vit_l14.npz
  - photos_sauce_crop/天天利美食坊（稠）/photo_5.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_3.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_11.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_7.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_1.jpeg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_10.jpg
  - app.py
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_11.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_14.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_1.jpg
-->

---
### Requirement: Social proof LIFF button and weight boost in random recommendation

The random nearby recommendation SHALL apply rating weight boost and include a LIFF ratings button.

#### Scenario: Random draw applies rating weights

- **WHEN** the system draws a random store from nearby candidates
- **THEN** stores with `must_eat` votes SHALL have weight = min(1.0 + votes × 0.5, 3.0)
- **AND** stores without votes SHALL have weight = 1.0

#### Scenario: Random recommendation Flex Message includes LIFF button

- **WHEN** the random recommendation Flex Message is built
- **THEN** the system SHALL include a「查看評價 💬」URIAction button linking to the LIFF ratings page for that store

<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->
---
### Requirement: Re-draw without re-sharing location

After receiving a random recommendation, the system SHALL include a「下一抽 🎲」Quick Reply button that allows the user to draw again without re-sharing their location.

When the user taps「下一抽 🎲」, the system SHALL use the saved `last_location` from the session and run the same random recommendation logic as the location event handler, including seen tracking, radius expansion, and exhaustion handling.

If no `last_location` exists in the session, the system SHALL reply with a prompt asking the user to share their location again.

#### Scenario: User taps 下一抽 after receiving recommendation

- **WHEN** the user taps「下一抽 🎲」
- **AND** a `last_location` exists in the session
- **THEN** the system SHALL run the same random recommendation logic and return a new Flex Message

#### Scenario: No saved location

- **WHEN** the user taps「下一抽 🎲」
- **AND** no `last_location` exists in the session
- **THEN** the system SHALL reply with a location prompt

<!-- @trace
source: random-surprise-redraw
updated: 2026-05-11
code:
  - app.py
-->

---
### Requirement: Share random recommendation with tagline

The random recommendation Flex Message SHALL include a「分享這家店 📤」LIFF button. When a tagline (籤詩 or far-distance phrase) is present, the share URL SHALL include a `tagline` parameter so the shared Flex Message displays the tagline text alongside the store name.

#### Scenario: Share includes tagline

- **WHEN** the random recommendation has a phrase (random_tagline or far_phrase)
- **THEN** the share URL SHALL include `&tagline=<encoded phrase>`
- **AND** the `/liff/share` page SHALL display the tagline prominently in the shared Flex Message

#### Scenario: Share without tagline

- **WHEN** the random recommendation has no phrase
- **THEN** the share URL SHALL omit the tagline parameter
- **AND** the `/liff/share` page SHALL display the standard store recommendation format

<!-- @trace
source: random-surprise-share-tagline
updated: 2026-05-11
code:
  - app.py
-->
