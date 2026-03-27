## ADDED Requirements

### Requirement: Few-shot examples loaded from file

The system SHALL load persona examples from a configurable JSON file at module initialization, and include them in the LLM prompt to guide the uncle's tone and humor style.

The examples file SHALL use the format: `[{"input": "...", "output": "..."}]`

#### Scenario: Examples file loaded successfully

- **WHEN** the uncle-persona module initializes and the examples file exists at the configured path
- **THEN** the module SHALL read all examples from the file and include them in the few-shot section of the prompt

#### Scenario: Missing examples file falls back to defaults

- **WHEN** the examples file does not exist at the configured path
- **THEN** the system SHALL fall back to built-in default examples and SHALL NOT raise an exception

#### Scenario: Examples path is configurable

- **WHEN** the module is initialized with a custom examples file path
- **THEN** the system SHALL load examples from that path instead of the default location
