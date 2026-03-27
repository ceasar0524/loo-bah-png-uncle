## ADDED Requirements

### Requirement: Noodle detection gate

Before performing positive/negative CLIP softmax, the system SHALL perform a binary noodle detection check. If the probability that the image contains noodles meets or exceeds a configurable threshold (default: 0.6), the system SHALL immediately return is_lu_rou_fan: false without proceeding to further classification.

#### Scenario: Noodle image rejected at gate

- **WHEN** an image with clearly visible noodles is provided (e.g., beef noodle soup)
- **THEN** the system SHALL return is_lu_rou_fan: false with confidence equal to (1.0 - noodle_prob) before evaluating positive/negative prompts

#### Scenario: Lu-rou-fan image passes gate

- **WHEN** an image of lu-rou-fan with no visible noodles is provided
- **THEN** the noodle_prob SHALL be below the threshold and the system SHALL proceed to positive/negative classification normally

## MODIFIED Requirements

### Requirement: Classify image as lu-rou-fan using CLIP zero-shot

The system SHALL use CLIP zero-shot classification to determine whether the input image contains lu-rou-fan (Taiwanese braised pork rice). The system SHALL first apply the noodle detection gate (see Noodle detection gate requirement). If the gate does not reject the image, the system SHALL compute cosine similarity between the image embedding and candidate text prompt embeddings, and return is_lu_rou_fan: true when the similarity meets or exceeds a configurable threshold (default: 0.72).

#### Scenario: Lu-rou-fan image classified correctly

- **WHEN** an image of lu-rou-fan is provided
- **THEN** the system SHALL return is_lu_rou_fan: true with confidence >= 0.72

#### Scenario: Non-lu-rou-fan image rejected

- **WHEN** an image of food that is not lu-rou-fan is provided
- **THEN** the system SHALL return is_lu_rou_fan: false

#### Scenario: Threshold configurable

- **WHEN** the caller specifies a custom classification threshold
- **THEN** the system SHALL apply that threshold instead of the default 0.72

#### Scenario: Non-food image rejected

- **WHEN** an image containing no food is provided
- **THEN** the system SHALL return is_lu_rou_fan: false with low confidence
