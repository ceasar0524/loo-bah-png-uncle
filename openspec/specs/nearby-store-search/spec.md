# nearby-store-search Specification

## Purpose

TBD - created by archiving change 'nearby-recommendation'. Update Purpose after archive.

## Requirements

### Requirement: Search nearby stores by style similarity

The system SHALL accept a matched store name and a user location (latitude, longitude), compute visual_profile similarity between the matched store and all other stores, filter stores within a configurable radius (default: 3 km), and return stores ranked by profile similarity score descending.

Visual profile similarity is computed by comparing four `visual_profile` fields with weighted scoring:
- `fat_ratio`: weight 0.3 (binary match)
- `skin`: weight 0.3 (binary match)
- `sauce_taste`: weight 0.3 (partial match: same = 1.0, one side is 均衡 = 0.5, otherwise 0.0)
- `sauce_color`: weight 0.1 (binary match)

`rice_quality` is excluded due to low discriminative power. `sauce_taste` supports partial scoring to handle stores with balanced flavor profiles.

Stores with a similarity score below 0.7 SHALL be excluded from results, regardless of distance.

The distance between user location and store location SHALL be computed using the Haversine formula.

Stores without a location entry in store_notes.json SHALL be excluded from results.

The system SHALL return at most 3 nearby store candidates. The persona layer SHALL present at most 2 stores to the user, ordered by distance ascending (nearest first).

#### Scenario: Nearby stores found within radius

- **WHEN** a matched store name and user location are provided and at least one store is within the radius with profile similarity above threshold
- **THEN** the system SHALL return up to 3 stores ordered by profile similarity score descending, each with store_name, similarity_score, and distance_km

#### Scenario: No stores within radius

- **WHEN** no store is within the configured radius
- **THEN** the system SHALL return an empty results list with `any_in_radius=False`

#### Scenario: Stores within radius but none pass similarity threshold

- **WHEN** at least one store is within the configured radius but none have similarity score ≥ 0.7
- **THEN** the system SHALL return an empty results list with `any_in_radius=True`

#### Scenario: Queried store excluded from results

- **WHEN** the matched store from the original recognition is within the radius
- **THEN** that store SHALL be excluded from the nearby recommendation results


<!-- @trace
source: nearby-recommendation
updated: 2026-04-10
code:
  - app.py
  - data/store_notes.json
  - haiku_features_cache_v2.json
  - src/nearby_search/__init__.py
  - eval_dino.py
  - src/nearby_search/searcher.py
  - src/uncle_persona/persona.py
  - src/pipeline.py
  - index_vit_l14.npz
-->

---
### Requirement: Store location data

Each store in store_notes.json SHALL have a `location` field containing `lat` (latitude) and `lng` (longitude) in decimal degrees.

#### Scenario: Store with location data

- **WHEN** a store has a valid `location.lat` and `location.lng` entry
- **THEN** the system SHALL include that store in the distance computation

#### Scenario: Store without location data

- **WHEN** a store has no `location` entry
- **THEN** the system SHALL skip that store in nearby search

<!-- @trace
source: nearby-recommendation
updated: 2026-04-10
code:
  - app.py
  - data/store_notes.json
  - haiku_features_cache_v2.json
  - src/nearby_search/__init__.py
  - eval_dino.py
  - src/nearby_search/searcher.py
  - src/uncle_persona/persona.py
  - src/pipeline.py
  - index_vit_l14.npz
-->

---
### Requirement: Random nearby store search mode

The system SHALL provide a `search_random_nearby_store(lat, lng, store_notes, seen)` function that selects one store randomly using a seen-based two-tier radius strategy:

1. Pick randomly from stores within 3 km (primary radius), until all primary stores have appeared in `seen`
2. Once all primary stores are in `seen`, expand to 3–5 km (extended radius)
3. Once all extended stores are also in `seen`, return None (caller resets `seen` and retries)
4. If no stores exist within 5 km at all, return None

The function SHALL NOT exclude seen stores from the random pool — it only uses `seen` to decide which tier to draw from. This allows natural repetition within a tier while ensuring eventual exploration of further stores.

This function SHALL operate independently from `search_nearby_stores` and SHALL NOT apply style similarity scoring or threshold filtering.

#### Scenario: Random store selected within primary radius

- **WHEN** `search_random_nearby_store` is called and not all primary stores (3 km) are in `seen`
- **THEN** the function SHALL return one randomly selected store from within 3 km

#### Scenario: Radius expanded to 5 km when all primary stores seen

- **WHEN** all stores within 3 km are in `seen` and at least one store exists within 3–5 km not yet in `seen`
- **THEN** the function SHALL return one randomly selected store from within 3–5 km

#### Scenario: All stores seen — reset signal

- **WHEN** all stores within 5 km are in `seen`
- **THEN** the function SHALL return None (caller resets `seen` and retries)

#### Scenario: No stores within extended radius

- **WHEN** no store exists within 5 km
- **THEN** the function SHALL return None

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