## ADDED Requirements

### Requirement: Resize image to maximum 1024px

The system SHALL resize the input image so that its longest side does not exceed 1024 pixels, preserving the original aspect ratio. Images smaller than 1024px on both sides SHALL NOT be upscaled.

#### Scenario: Large image resized

- **WHEN** an image with longest side greater than 1024px is provided
- **THEN** the system SHALL return an image with longest side equal to 1024px and aspect ratio preserved

#### Scenario: Small image not upscaled

- **WHEN** an image with both sides smaller than 1024px is provided
- **THEN** the system SHALL return the image at its original dimensions

### Requirement: Brightness normalization using CLAHE

The system SHALL apply CLAHE (Contrast Limited Adaptive Histogram Equalization) on the L channel of the LAB color space to normalize brightness, using clip_limit=2.0 and tileGridSize=8 as default parameters.

#### Scenario: Dark image normalized

- **WHEN** an underexposed image is provided
- **THEN** the system SHALL return an image with improved local contrast in dark regions

#### Scenario: Well-lit image minimally affected

- **WHEN** a well-exposed image is provided
- **THEN** the system SHALL return an image with minimal visual change due to CLAHE

### Requirement: Preprocessing pipeline is identical at index build time and query time

The system SHALL expose a single preprocessing function used by both store-embedding-db (index build) and visual-recognition (query). No separate or divergent preprocessing paths SHALL exist.

#### Scenario: Same function called by both modules

- **WHEN** store-embedding-db builds the index and when visual-recognition processes a query image
- **THEN** both SHALL call the same preprocessing function with the same default parameters

### Requirement: Unsupported or corrupted files handled gracefully

The system SHALL skip files that cannot be read or decoded, log a warning with the file path, and continue processing without raising an exception.

#### Scenario: Corrupted image skipped

- **WHEN** a file cannot be opened or decoded as an image
- **THEN** the system SHALL log a warning and return None without raising an exception

#### Scenario: Unsupported format skipped

- **WHEN** a file with a format other than JPEG or PNG is provided
- **THEN** the system SHALL log a warning and return None without raising an exception
