## MODIFIED Requirements

### Requirement: Non-image message handling

The system SHALL handle the following text keywords in `handle_text`:
- 隨機驚喜: triggers random nearby recommendation flow
- 巷子口: triggers hidden gems district selection
- 個人化: triggers the taste preference quiz flow
- 統計 (admin only): returns usage statistics

All other text messages SHALL be silently ignored. No reply SHALL be sent.

#### Scenario: User sends 個人化

- **WHEN** a LINE user sends the text message「個人化」
- **THEN** the system SHALL reply with the first taste quiz question and Quick Reply buttons
- **AND** the system SHALL store the quiz state in the user's session

#### Scenario: User sends an unrecognized text message

- **WHEN** a LINE user sends a text message that does not match any keyword
- **THEN** the system SHALL not reply and SHALL return HTTP 200 to LINE

---

## ADDED Requirements

### Requirement: Handle taste quiz Quick Reply responses

The system SHALL handle Quick Reply responses during an active taste quiz session.

When a user has an active `taste_quiz` session and sends a message matching one of the quiz answer options, the system SHALL record the answer and advance the quiz.

#### Scenario: User answers a quiz question mid-flow

- **WHEN** a user with an active `taste_quiz` session taps a Quick Reply button
- **THEN** the system SHALL store the answer, advance to the next question or prompt for location if all four answers are collected

### Requirement: Handle location message with taste session

The system SHALL handle location messages when the user has a completed taste quiz session (`__taste__`).

Upon receiving the location, the system SHALL run taste-based store matching and reply with a Flex Message listing 2–3 stores.

#### Scenario: Location received with taste session

- **WHEN** a location message is received and the session value is `"__taste__"`
- **THEN** the system SHALL run taste-based matching using stored preferences and return a Flex Message recommendation

---

### Requirement: 附近巷仔口店家 keyword

The system SHALL handle the keyword「附近巷仔口店家」as a dedicated trigger for nearby hidden gems lookup using a saved location.

「巷仔口」SHALL always show the standard district selection menu regardless of session state.

#### Scenario: User sends 附近巷仔口店家 with saved location

- **WHEN** a user sends「附近巷仔口店家」
- **AND** a `last_location` is saved in the session
- **THEN** the system SHALL query hidden gems within 3 km and return a Flex Message (up to 3 stores)
- **AND** the system SHALL clear `last_location` from the session

#### Scenario: User sends 附近巷仔口店家 without saved location

- **WHEN** a user sends「附近巷仔口店家」
- **AND** no `last_location` exists in the session
- **THEN** the system SHALL not reply
