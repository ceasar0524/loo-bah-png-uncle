## ADDED Requirements

### Requirement: Leave-one-out evaluation

The system SHALL provide an evaluation mode that measures recognition accuracy by iterating over all photos: for each photo, temporarily excluding it from the index and using the remaining photos to predict its store, then comparing the prediction against the ground truth label.

#### Scenario: Overall accuracy reported

- **WHEN** leave-one-out evaluation completes
- **THEN** the system SHALL print the overall recognition accuracy as a percentage (correct predictions / total photos)

#### Scenario: Per-store accuracy reported

- **WHEN** leave-one-out evaluation completes
- **THEN** the system SHALL print the accuracy for each individual store, ordered by accuracy ascending (worst stores first)

### Requirement: Confusion summary reported

The system SHALL identify and report which stores are most frequently confused with each other during leave-one-out evaluation.

#### Scenario: Most confused store pairs identified

- **WHEN** leave-one-out evaluation completes
- **THEN** the system SHALL print the top confused store pairs (e.g., "Store A predicted as Store B: 3 times")
