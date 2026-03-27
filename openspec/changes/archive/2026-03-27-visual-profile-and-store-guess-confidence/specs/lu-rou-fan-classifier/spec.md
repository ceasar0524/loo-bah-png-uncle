## ADDED Requirements

### Requirement: Extract visual features in same Haiku call as classification

The classifier SHALL extract visual features alongside classification in a single Claude Haiku API call to minimise latency and cost. When `is_lu_rou_fan` is true, the classifier SHALL return the following additional fields extracted from the image:

- `bowl_color`: one of `bright_green`, `olive_green`, `light_gray_green`, `white`, `yellow`, `red`, `black`, `brown`, `other`
- `bowl_shape`: one of `round_bowl`, `wide_flat_plate`, `rectangular_box`, `other`
- `bowl_texture`: one of `matte_ceramic`, `glossy_ceramic`, `plastic`, `styrofoam`, `other`
- `toppings`: list of detected toppings from the standard topping vocabulary

The model prompt SHALL provide precise descriptions distinguishing visually similar bowl colours (e.g. `bright_green` as vivid neon green vs `olive_green` as dark muted green vs `light_gray_green` as pale green-gray).

#### Scenario: Bowl features returned with lu-rou-fan classification

- **WHEN** an image is classified as lu-rou-fan
- **THEN** the result SHALL include `bowl_color`, `bowl_shape`, `bowl_texture`, and `toppings` fields populated from the single Haiku call

#### Scenario: Bowl features absent for non-lu-rou-fan

- **WHEN** an image is classified as not lu-rou-fan
- **THEN** `bowl_color`, `bowl_shape`, `bowl_texture` SHALL be `None` and `toppings` SHALL be an empty list

#### Scenario: Single API call for both classification and features

- **WHEN** classification is performed
- **THEN** the system SHALL make exactly one Claude Haiku API call that returns both the yes/no classification and all visual feature fields
