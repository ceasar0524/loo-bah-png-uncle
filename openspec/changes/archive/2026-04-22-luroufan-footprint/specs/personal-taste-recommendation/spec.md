## ADDED Requirements

### Requirement: Photo recognition response includes check-in entry point

The system SHALL include a check-in Quick Reply button in the photo recognition response, depending on the recognition outcome.

When recognition identifies a single store with high confidence, the system SHALL:
1. Store the identified store name in the user session under `pending_checkin`
2. Append a Quick Reply button「就是這家 ✅」to the response

When recognition results in a tie or complete failure, the system SHALL:
1. Append a Quick Reply button「打卡這碗 📍」to the response

#### Scenario: High-confidence recognition — check-in button appended

- **WHEN** photo recognition identifies a store with high confidence
- **THEN** the system SHALL store the store name in session `pending_checkin`
- **AND** include「就是這家 ✅」as a Quick Reply button alongside existing Quick Reply options

#### Scenario: Tie or failure recognition — rescue button appended

- **WHEN** photo recognition results in a tie or complete failure
- **THEN** the system SHALL include「打卡這碗 📍」as a Quick Reply button alongside existing Quick Reply options
