# index-builder-cli Specification

## Purpose

TBD - created by archiving change 'recognizer-cli'. Update Purpose after archive.

## Requirements

### Requirement: Index builder CLI accepts photos directory argument

The system SHALL provide a `build_index.py` script that accepts a root directory path containing per-store photo subdirectories and builds the embedding index by calling the store-embedding-db module.

#### Scenario: Index built from directory argument

- **WHEN** `python build_index.py --photos <dir> --output <path>` is executed
- **THEN** the system SHALL traverse the directory, build the embedding index, and save it to the specified output path

#### Scenario: Build summary printed on completion

- **WHEN** index building completes successfully
- **THEN** the system SHALL print the number of stores indexed and total photos processed

#### Scenario: Missing directory handled gracefully

- **WHEN** the provided photos directory does not exist
- **THEN** the system SHALL print a user-friendly error message in Traditional Chinese and exit with a non-zero code
