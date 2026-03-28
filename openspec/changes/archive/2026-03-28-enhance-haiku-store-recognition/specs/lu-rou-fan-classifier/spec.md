## MODIFIED Requirements

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
