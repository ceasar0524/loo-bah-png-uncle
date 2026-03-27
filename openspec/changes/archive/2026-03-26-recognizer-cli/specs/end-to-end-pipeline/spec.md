## ADDED Requirements

### Requirement: End-to-end pipeline from image to uncle-persona response

The system SHALL provide a pipeline function that accepts an image path and executes the full recognition flow in order: image-preprocessing → visual-recognition → store-matching (if lu-rou-fan) → uncle-persona, and returns the uncle-persona response string.

#### Scenario: Full pipeline runs successfully

- **WHEN** a valid image path of a lu-rou-fan photo is provided
- **THEN** the system SHALL return the uncle-persona response string after completing all pipeline stages

#### Scenario: Non-lu-rou-fan image skips store-matching

- **WHEN** visual-recognition returns is_lu_rou_fan: false
- **THEN** the system SHALL skip store-matching and pass the visual result directly to uncle-persona

#### Scenario: Pipeline function importable by other modules

- **WHEN** a Line Bot or web layer imports the pipeline module
- **THEN** it SHALL be able to call the pipeline function directly without invoking the CLI

### Requirement: CLI entry point accepts image path argument

The system SHALL provide a `recognize.py` script that accepts a single positional argument (image file path) and prints the uncle-persona response to stdout.

#### Scenario: Response printed to stdout

- **WHEN** `python recognize.py <image_path>` is executed with a valid image
- **THEN** the uncle-persona response SHALL be printed to stdout

#### Scenario: Missing file handled gracefully

- **WHEN** the provided image path does not exist
- **THEN** the system SHALL print a user-friendly error message in Traditional Chinese and exit with a non-zero code

#### Scenario: Missing API key handled gracefully

- **WHEN** the ANTHROPIC_API_KEY environment variable is not set
- **THEN** the system SHALL print a clear Traditional Chinese message instructing the user to set it and exit

### Requirement: Model loading progress indicated

The system SHALL print a loading indicator when the CLIP model is being loaded, so the user is aware the system is working and not frozen.

#### Scenario: Loading message shown during model init

- **WHEN** the CLIP model is loading for the first time
- **THEN** the system SHALL print a message such as "載入模型中..." to stdout before the model is ready
