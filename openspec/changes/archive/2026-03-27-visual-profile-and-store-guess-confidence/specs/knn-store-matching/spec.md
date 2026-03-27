## ADDED Requirements

### Requirement: Haiku feature override for high-confidence distinctive features

After the CLIP KNN result is computed, the system SHALL apply a Haiku feature override when the classifier has detected a high-confidence distinctive visual feature that uniquely identifies a store.

The override SHALL consult `data/store_notes.json` for each store's `bowl` entry and `known_toppings`. The override scoring SHALL be:

- Bowl color match on a store marked `distinctive: true`: +0.5
- Bowl shape match on a store marked `distinctive: true`: +0.2
- Bowl texture match on a store marked `distinctive: true`: +0.3
- Cilantro (`cilantro`) detected and present in a store's `known_toppings`: +0.8
- Other topping detected and present in a store's `known_toppings`: +0.3

The override SHALL only fire when a single store reaches or exceeds the override threshold (default: 0.5) with no tie. If multiple stores reach the threshold simultaneously, the override SHALL be suppressed and the CLIP result SHALL be used.

When the override fires, the matched store SHALL be returned with `confidence_level: "high"` regardless of the underlying CLIP similarity score.

When the override does not fire, the CLIP KNN result SHALL be returned unchanged.

#### Scenario: Distinctive bowl colour triggers override

- **WHEN** the classifier detects `bowl_color: "bright_green"` and store 晴光小吃 has `bowl.color: "bright_green"` with `distinctive: true`
- **THEN** the system SHALL override the CLIP result and return 晴光小吃 with `confidence_level: "high"`

#### Scenario: Cilantro triggers override for 阿興

- **WHEN** the classifier detects `cilantro` in toppings and 阿興魯肉飯 has `cilantro` in `known_toppings`
- **THEN** the system SHALL override the CLIP result and return 阿興魯肉飯 with `confidence_level: "high"`

#### Scenario: Override suppressed when multiple stores qualify

- **WHEN** detected features match more than one store above the override threshold
- **THEN** the system SHALL suppress the override and return the CLIP KNN result unchanged

#### Scenario: No distinctive features falls back to CLIP

- **WHEN** no detected feature scores any store at or above the override threshold
- **THEN** the system SHALL return the CLIP KNN result unchanged
