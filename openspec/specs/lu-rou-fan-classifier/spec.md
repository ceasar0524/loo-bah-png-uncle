# lu-rou-fan-classifier Specification

## Purpose

TBD - created by archiving change 'visual-recognition'. Update Purpose after archive.

## Requirements

### Requirement: Classify image as lu-rou-fan using CLIP zero-shot

The system SHALL use Claude Haiku vision API to determine whether the input image contains lu-rou-fan (Taiwanese braised pork rice). The system SHALL send the image to the Claude Haiku model along with a classification prompt that requests a JSON response. The model SHALL respond with a single JSON object containing `is_lu_rou_fan` ("yes" or "no"), `confidence` (integer 0–10), and visual feature fields. The system SHALL return is_lu_rou_fan: true only when `is_lu_rou_fan` is "yes" AND the normalized confidence (`confidence` / 10.0) meets or exceeds a configurable threshold (default: 0.5).

If the model response cannot be parsed as valid JSON, the system SHALL fall back to returning is_lu_rou_fan: false with confidence 0.0.

#### Scenario: Lu-rou-fan image classified correctly

- **WHEN** an image of lu-rou-fan is provided
- **THEN** the system SHALL return is_lu_rou_fan: true with confidence >= 0.5

#### Scenario: Non-lu-rou-fan image rejected

- **WHEN** an image of food that is not lu-rou-fan is provided
- **THEN** the system SHALL return is_lu_rou_fan: false

#### Scenario: Threshold configurable

- **WHEN** the caller specifies a custom classification threshold
- **THEN** the system SHALL apply that threshold instead of the default 0.5

#### Scenario: Non-food image rejected

- **WHEN** an image containing no food is provided
- **THEN** the system SHALL return is_lu_rou_fan: false with low confidence

#### Scenario: Contradictory model response rejected

- **WHEN** the model JSON contains is_lu_rou_fan "no" but a high confidence score
- **THEN** the system SHALL return is_lu_rou_fan: false because the "yes" condition is not met

#### Scenario: JSON parse failure falls back to false

- **WHEN** the model returns a response that cannot be parsed as valid JSON
- **THEN** the system SHALL return is_lu_rou_fan: false with confidence 0.0

---
### Requirement: Return confidence score

The system SHALL return a confidence score between 0.0 and 1.0 representing the Claude Haiku vision model's normalized confidence. The raw 0–10 integer score from the model SHALL be divided by 10.0 to produce the normalized value.

#### Scenario: Confidence score in valid range

- **WHEN** classification is performed on any image
- **THEN** the returned confidence value SHALL be a float between 0.0 and 1.0

---
### Requirement: Extract visual features in same Haiku call as classification

The classifier SHALL extract visual features alongside classification in a single Claude Haiku API call to minimise latency and cost. When `is_lu_rou_fan` is true, the classifier SHALL return the following additional fields extracted from the image:

- `bowl_color`: one of `bright_green`, `olive_green`, `light_gray_green`, `white`, `yellow`, `red`, `black`, `brown`, `other`
- `bowl_shape`: one of `round_bowl`, `wide_flat_plate`, `rectangular_box`, `other`
- `bowl_texture`: one of `matte_ceramic`, `glossy_ceramic`, `plastic`, `styrofoam`, `other`
- `toppings`: list of detected toppings from the standard topping vocabulary: `cilantro`, `braised_egg`, `soft_boiled_egg`, `pork_floss`, `pickled_radish`, `pickled_cucumber`, `green_onion`, `cucumber`, `yin_gua`

The model prompt SHALL provide precise descriptions distinguishing visually similar bowl colours (e.g. `bright_green` as vivid neon green vs `olive_green` as dark muted green vs `light_gray_green` as pale green-gray).

The model prompt SHALL include descriptions distinguishing visually similar pickled vegetables: `pickled_radish` is yellow pickled daikon; `pickled_cucumber` is dark-colored braised cucumber (醬瓜); `cucumber` is fresh cucumber.

#### Scenario: Bowl features returned with lu-rou-fan classification

- **WHEN** an image is classified as lu-rou-fan
- **THEN** the result SHALL include `bowl_color`, `bowl_shape`, `bowl_texture`, and `toppings` fields populated from the single Haiku call

#### Scenario: Bowl features absent for non-lu-rou-fan

- **WHEN** an image is classified as not lu-rou-fan
- **THEN** `bowl_color`, `bowl_shape`, `bowl_texture` SHALL be `None` and `toppings` SHALL be an empty list

#### Scenario: Single API call for both classification and features

- **WHEN** classification is performed
- **THEN** the system SHALL make exactly one Claude Haiku API call that returns both the yes/no classification and all visual feature fields

#### Scenario: yin_gua detected as topping

- **WHEN** Oriental pickling melon (蔭瓜) is visible in the image
- **THEN** the classifier SHALL include `yin_gua` in the toppings list

#### Scenario: pickled_cucumber distinguished from pickled_radish

- **WHEN** dark-colored braised cucumber (醬瓜) is visible in the image
- **THEN** the classifier SHALL return `pickled_cucumber`, not `pickled_radish`

#### Scenario: pickled_radish distinguished from pickled_cucumber

- **WHEN** yellow pickled daikon is visible in the image
- **THEN** the classifier SHALL return `pickled_radish`, not `pickled_cucumber`


<!-- @trace
source: enhance-haiku-store-recognition
updated: 2026-03-28
code:
  - data/store_notes.json
  - src/visual_recognition/classifier.py
-->

---
### Requirement: Result conforms to visual-recognition-schema

The classifier SHALL return a result conforming to the visual-recognition-schema defined in data-schema, including is_lu_rou_fan and confidence fields.

#### Scenario: Non-lu-rou-fan result has empty feature fields

- **WHEN** is_lu_rou_fan is false
- **THEN** all feature fields (toppings, meat_cut, sauce_color, rice_quality) SHALL be None or empty