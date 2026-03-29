## MODIFIED Requirements

### Requirement: Detect toppings using binary CLIP classification

The system SHALL detect toppings from the image using the Claude Haiku vision classifier. Topping detection is performed in the same API call as lu-rou-fan classification, returning a list of detected toppings from the standard vocabulary: cilantro, braised_egg, soft_boiled_egg, pork_floss, pickled_radish, green_onion, pickled_cucumber, yin_gua.

The CLIP-based binary topping detection is superseded by Haiku vision and SHALL NOT be used.

The standard topping vocabulary includes: cilantro, braised_egg, soft_boiled_egg, hard_boiled_egg, pork_floss, pickled_radish, green_onion, pickled_cucumber, yin_gua, oyster, shredded_chicken, braised_cabbage.

- `pickled_radish`: Bright yellow pickled daikon slices placed directly on top of the rice. The classifier SHALL NOT report `pickled_radish` based on bowl background, table surface, or non-food objects of similar colour.
- `pickled_cucumber`: Pickled cucumber slices, bright green colour.
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
