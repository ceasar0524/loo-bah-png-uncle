## MODIFIED Requirements

### Requirement: Classify image as lu-rou-fan using CLIP zero-shot

The system SHALL use Claude Haiku vision API to determine whether the input image contains lu-rou-fan (Taiwanese braised pork rice). The system SHALL send the image to the Claude Haiku model along with a classification prompt. The model SHALL respond with a yes/no answer on the first line and an integer confidence score from 0 to 10 on the second line. The system SHALL return is_lu_rou_fan: true only when the answer is "yes" AND the normalized confidence (score / 10.0) meets or exceeds a configurable threshold (default: 0.5).

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

- **WHEN** the model returns answer "no" but a high confidence score
- **THEN** the system SHALL return is_lu_rou_fan: false because the "yes" condition is not met

---

### Requirement: Return confidence score

The system SHALL return a confidence score between 0.0 and 1.0 representing the Claude Haiku vision model's normalized confidence. The raw 0–10 integer score from the model SHALL be divided by 10.0 to produce the normalized value.

#### Scenario: Confidence score in valid range

- **WHEN** classification is performed on any image
- **THEN** the returned confidence value SHALL be a float between 0.0 and 1.0

---

## REMOVED Requirements

### Requirement: Noodle detection gate

**Reason**: The noodle detection gate was introduced as a workaround to handle CLIP's inability to distinguish noodle dishes from lu-rou-fan. Claude Haiku vision can natively distinguish noodle dishes without a separate gate step.
**Migration**: No migration needed. The noodle detection logic in `classify()` SHALL be removed entirely. Claude Haiku will reject noodle dishes through its general visual understanding.

#### Scenario: Noodle image rejected by vision model

- **WHEN** an image with clearly visible noodles is provided (e.g., beef noodle soup)
- **THEN** the system SHALL return is_lu_rou_fan: false via the Claude Haiku answer "no"
