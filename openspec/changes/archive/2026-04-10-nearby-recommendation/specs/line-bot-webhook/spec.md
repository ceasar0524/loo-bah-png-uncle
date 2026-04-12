# line-bot-webhook delta Specification

## ADDED Requirements

### Requirement: Quick Reply button after recognition response

After sending a recognition response where `is_lu_rou_fan` is true and matches is non-empty, the system SHALL append a Quick Reply button labeled「找附近類似的 📍」to the response message.

#### Scenario: Quick Reply button shown after successful recognition

- **WHEN** the recognition result has `is_lu_rou_fan: true` and at least one store match
- **THEN** the LINE response SHALL include a Quick Reply button labeled「找附近類似的 📍」

#### Scenario: Quick Reply button not shown for non-lu-rou-fan

- **WHEN** the recognition result has `is_lu_rou_fan: false`
- **THEN** the LINE response SHALL NOT include the Quick Reply button

### Requirement: Handle Quick Reply button tap

When the user taps the Quick Reply button, the system SHALL reply with a location-request message asking the user to share their current location.

#### Scenario: User taps Quick Reply button

- **WHEN** the system receives a postback or message event matching the Quick Reply action
- **THEN** the system SHALL send a message prompting the user to share their location

### Requirement: Handle location message

The system SHALL handle LINE location message events. Upon receiving a location message, the system SHALL retrieve the stored query vector for that user, run nearby store search, and send the uncle persona's nearby recommendation response.

#### Scenario: Location received with valid session

- **WHEN** a location message is received and a query vector exists in session for that user
- **THEN** the system SHALL run nearby store search and return the uncle persona recommendation response

#### Scenario: Location received with expired session

- **WHEN** a location message is received but no query vector exists in session for that user
- **THEN** the system SHALL respond asking the user to send a photo first
