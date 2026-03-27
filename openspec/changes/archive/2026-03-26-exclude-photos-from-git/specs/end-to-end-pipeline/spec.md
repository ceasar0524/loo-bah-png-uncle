## ADDED Requirements

### Requirement: Training photos excluded from version control

The `photos/` directory SHALL be listed in `.gitignore` to prevent training photos from being committed to the repository. The vector index (`index.npz`) SHALL remain under version control as it is required for store matching at runtime.

#### Scenario: photos/ not tracked by git

- **WHEN** a developer runs `git status` or `git add .`
- **THEN** files under `photos/` SHALL NOT appear as tracked or staged files
