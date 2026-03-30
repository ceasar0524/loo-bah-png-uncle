# visual-feature-recognizer Specification

## Purpose

TBD - created by archiving change 'visual-recognition'. Update Purpose after archive.

## Requirements

### Requirement: Detect toppings using binary CLIP classification

The system SHALL detect toppings from the image using the Claude Haiku vision classifier. Topping detection is performed in the same API call as lu-rou-fan classification, returning a list of detected toppings from the standard vocabulary: cilantro, egg, pork_floss, pickled_radish, green_onion, pickled_cucumber, yin_gua.

The CLIP-based binary topping detection is superseded by Haiku vision and SHALL NOT be used.

The standard topping vocabulary includes: cilantro, egg, pork_floss, pickled_radish, green_onion, pickled_cucumber, yin_gua, oyster, shredded_chicken, braised_cabbage.

- `egg`: Any egg placed on top of the rice, including braised egg (滷蛋), soft-boiled egg (溏心蛋), or fried egg (荷包蛋). The classifier SHALL use a single `egg` label regardless of egg type. Store-specific display names (e.g. 溏心蛋, 半熟荷包蛋, 魯蛋) SHALL be resolved from `store_notes.json` `topping_names` at persona response time.
- `pickled_radish`: Bright yellow pickled daikon slices placed directly on top of the rice. The classifier SHALL NOT report `pickled_radish` based on bowl background, table surface, or non-food objects of similar colour.
- `cilantro`: Fresh herb with flat jagged leaves and thin stems. The classifier SHALL NOT report `cilantro` based on flat round slices or other non-herb green garnishes; visible herb leaf structure is required.
- `pickled_cucumber`: Pickled cucumber slices, bright green flat round discs.
- `yin_gua`: Dark brown soft braised melon chunks, deep soy-sauce colour — visually distinct from `pickled_cucumber`.

The classifier SHALL return a `bowl_color` field using the following vocabulary:
`bright_green` | `olive_green` | `light_gray_green` | `white` | `yellow` | `red` | `black` | `brown` | `silver` (stainless steel metallic) | `other`

The classifier SHALL return a `bowl_texture` field using the following vocabulary:
`matte_ceramic` | `glossy_ceramic` | `plastic` | `styrofoam` | `metal` | `other`

#### Scenario: Cilantro detected

- **WHEN** the image contains visible cilantro on the lu-rou-fan
- **THEN** the Haiku classifier SHALL include "cilantro" in the toppings list

#### Scenario: No toppings detected

- **WHEN** the image shows plain lu-rou-fan with no identifiable toppings
- **THEN** the system SHALL return an empty toppings list

#### Scenario: Multiple toppings detected simultaneously

- **WHEN** the image contains both braised egg and pickled radish
- **THEN** both SHALL be included in the toppings list

#### Scenario: pickled_radish not reported from table background

- **WHEN** the image shows lu-rou-fan on a yellow wooden table with no pickled radish on the rice
- **THEN** the classifier SHALL NOT include "pickled_radish" in the toppings list


<!-- @trace
source: tune-haiku-override-and-add-stores
updated: 2026-03-29
code:
  - src/visual_recognition/classifier.py
  - data/store_notes.json
  - eval_hybrid.py
-->

---
### Requirement: Classify pork part from configurable categories

The system SHALL classify the pork part using CLIP zero-shot classification. Default categories: belly (五花), fatty (肥肉多), lean (瘦肉多), skin_heavy (皮多). The result is used for uncle-persona food description only and SHALL NOT be used for store matching.

#### Scenario: Pork part classified by highest CLIP similarity

- **WHEN** pork part classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Missing pork part config falls back to defaults

- **WHEN** the pork_parts config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

---
### Requirement: Classify fat-to-lean ratio from configurable categories

The system SHALL classify the fat-to-lean ratio of the pork using CLIP zero-shot classification. Default categories: fat_heavy (7:3), balanced (5:5), lean_heavy (3:7). The result is used for uncle-persona food description only and SHALL NOT be used for store matching.

#### Scenario: Fat ratio classified by highest CLIP similarity

- **WHEN** fat ratio classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Missing fat ratio config falls back to defaults

- **WHEN** the fat_ratio config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

---
### Requirement: Detect pork skin presence from configurable categories

The system SHALL classify whether the pork includes skin using CLIP zero-shot classification. Default categories: with_skin, no_skin. The result is used for uncle-persona food description only and SHALL NOT be used for store matching.

#### Scenario: Pork with skin detected

- **WHEN** the image shows braised pork with visible skin and gelatinous texture
- **THEN** the system SHALL return skin: "with_skin"

#### Scenario: Missing skin config falls back to defaults

- **WHEN** the skin config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

---
### Requirement: Classify sauce color from configurable categories

The system SHALL classify the braising sauce color using CLIP zero-shot classification. Default categories: light, medium, dark, black_gold. The result is used for uncle-persona food description only and SHALL NOT be used for store matching.

#### Scenario: Sauce color classified by highest CLIP similarity

- **WHEN** sauce color classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Missing sauce color config falls back to defaults

- **WHEN** the sauce_colors config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

---
### Requirement: Classify rice quality from configurable categories

The system SHALL classify the rice texture using CLIP zero-shot classification. Default categories: fluffy, soft, mushy. The result is used for uncle-persona food description only and SHALL NOT be used for store matching.

#### Scenario: Rice quality classified by highest CLIP similarity

- **WHEN** rice quality classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Missing rice quality config falls back to defaults

- **WHEN** the rice_qualities config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

---
### Requirement: Feature recognition only runs on confirmed lu-rou-fan

The system SHALL only perform CLIP feature recognition when is_lu_rou_fan is true. If the classifier returns false, all feature fields SHALL be skipped and set to None or empty.

#### Scenario: Feature recognition skipped for non-lu-rou-fan

- **WHEN** the lu-rou-fan classifier returns is_lu_rou_fan: false
- **THEN** the system SHALL NOT invoke CLIP feature recognition and SHALL return None for all feature fields