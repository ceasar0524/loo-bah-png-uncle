## MODIFIED Requirements

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
