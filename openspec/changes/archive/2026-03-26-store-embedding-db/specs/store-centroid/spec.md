## ADDED Requirements

### Requirement: Store all photo vectors for KNN matching

The system SHALL store every individual photo embedding along with its store label and photo count per store in the index, enabling KNN-based matching rather than centroid comparison.

#### Scenario: All vectors stored with store labels

- **WHEN** the index is built
- **THEN** every photo embedding SHALL be stored with its corresponding store name as a label

#### Scenario: photo_count stored per store

- **WHEN** the index is built
- **THEN** each store's total photo count SHALL be stored in the index for use by the matching module

#### Scenario: New store can be appended by rebuilding

- **WHEN** new store photos are added to the dataset directory
- **THEN** the system SHALL rebuild the full index to include the new store's vectors
