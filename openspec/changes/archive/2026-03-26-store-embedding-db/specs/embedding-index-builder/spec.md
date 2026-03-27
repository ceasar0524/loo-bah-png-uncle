## ADDED Requirements

### Requirement: Build embedding index from store photos

The system SHALL process all photos organized in per-store directories and generate a CLIP embedding vector for each photo, then persist the index to disk.

#### Scenario: Index built from directory structure

- **WHEN** a root directory containing subdirectories named by store is provided
- **THEN** the system SHALL traverse each subdirectory, embed all JPEG/PNG images, and store the vectors with their store labels

### Requirement: Preprocessing consistency

The system SHALL apply the same image preprocessing pipeline (resize to max 1024px, brightness normalization) to each photo before generating its CLIP embedding, ensuring consistency with query-time preprocessing.

#### Scenario: Preprocessing applied before embedding

- **WHEN** a photo is processed during index building
- **THEN** the system SHALL apply resize and brightness normalization before passing the image to CLIP

#### Scenario: Preprocessed and raw images produce consistent embeddings

- **WHEN** the same photo is preprocessed at index build time and query time using identical steps
- **THEN** the resulting embeddings SHALL be comparable in the same vector space

#### Scenario: Index persisted to disk

- **WHEN** embedding generation completes
- **THEN** the system SHALL save the index as a .npz file containing all vectors, store labels, centroids, and photo counts

#### Scenario: Unsupported file skipped

- **WHEN** a file in a store directory is not JPEG or PNG
- **THEN** the system SHALL skip that file, log a warning, and continue processing without interruption

#### Scenario: Corrupted image skipped

- **WHEN** an image file cannot be read or decoded
- **THEN** the system SHALL skip that file, log a warning, and continue processing without interruption

### Requirement: Index integrity check

The system SHALL report the number of stores and total photos indexed upon build completion.

#### Scenario: Build summary reported

- **WHEN** index build finishes
- **THEN** the system SHALL print the count of stores indexed and total photos successfully processed
