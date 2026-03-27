## ADDED Requirements

### Requirement: Classify image as lu-rou-fan using CLIP zero-shot

The system SHALL use CLIP zero-shot classification to determine whether the input image contains lu-rou-fan (Taiwanese braised pork rice). The system SHALL compute cosine similarity between the image embedding and candidate text prompt embeddings, and return is_lu_rou_fan: true when the similarity meets or exceeds a configurable threshold (default: 0.6).

#### Scenario: Lu-rou-fan image classified correctly

- **WHEN** an image of lu-rou-fan is provided
- **THEN** the system SHALL return is_lu_rou_fan: true with confidence >= 0.6

#### Scenario: Non-lu-rou-fan image rejected

- **WHEN** an image of food that is not lu-rou-fan is provided
- **THEN** the system SHALL return is_lu_rou_fan: false

#### Scenario: Threshold configurable

- **WHEN** the caller specifies a custom classification threshold
- **THEN** the system SHALL apply that threshold instead of the default 0.6

#### Scenario: Non-food image rejected

- **WHEN** an image containing no food is provided
- **THEN** the system SHALL return is_lu_rou_fan: false with low confidence

### Requirement: Return confidence score

The system SHALL return a confidence score between 0.0 and 1.0 representing the CLIP cosine similarity between the image and the lu-rou-fan text prompt.

#### Scenario: Confidence score in valid range

- **WHEN** classification is performed on any image
- **THEN** the returned confidence value SHALL be a float between 0.0 and 1.0

### Requirement: Result conforms to visual-recognition-schema

The classifier SHALL return a result conforming to the visual-recognition-schema defined in data-schema, including is_lu_rou_fan and confidence fields.

#### Scenario: Non-lu-rou-fan result has empty feature fields

- **WHEN** is_lu_rou_fan is false
- **THEN** all feature fields (toppings, meat_cut, sauce_color, rice_quality) SHALL be None or empty
