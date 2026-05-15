## ADDED Requirements

### Requirement: Handle taste quiz Quick Reply responses

The system SHALL handle Quick Reply responses during an active taste quiz session.

When a user has an active `taste_quiz` session and sends a message matching one of the quiz answer options, the system SHALL record the answer and advance the quiz.

After all four answers are collected, the system SHALL store the answers in a `taste_save_pending` session key and ask the user whether to save preferences, with Quick Reply buttons「儲存 ✅」and「不用 ❌」.

#### Scenario: User answers a quiz question mid-flow

- **WHEN** a user with an active `taste_quiz` session taps a Quick Reply button
- **THEN** the system SHALL store the answer and advance to the next question

#### Scenario: User completes all four questions

- **WHEN** a user answers the fourth quiz question
- **THEN** the system SHALL store all answers in `taste_save_pending`
- **AND** reply asking whether to save preferences with Quick Reply「儲存 ✅」/「不用 ❌」

---

## ADDED Requirements

### Requirement: Handle preference save confirmation

The system SHALL handle「儲存 ✅」and「不用 ❌」responses when a `taste_save_pending` session key exists.

#### Scenario: User taps 儲存

- **WHEN** a user taps「儲存 ✅」and `taste_save_pending` exists in the session
- **THEN** the system SHALL write preferences to Firestore
- **AND** clear `taste_save_pending` from the session
- **AND** set session store to `__taste__` and prompt for location

#### Scenario: User taps 不用

- **WHEN** a user taps「不用 ❌」and `taste_save_pending` exists in the session
- **THEN** the system SHALL clear `taste_save_pending` from the session
- **AND** set session store to `__taste__` and prompt for location

---

### Requirement: Handle 直接用 and 重新填 Quick Reply responses

The system SHALL handle「直接用 ✅」and「重新填 🔄」when a `taste_loaded` session key exists.

#### Scenario: User taps 直接用

- **WHEN** a user taps「直接用 ✅」and `taste_loaded` exists in the session
- **THEN** the system SHALL use the loaded preferences, set session store to `__taste__`, and prompt for location

#### Scenario: User taps 重新填

- **WHEN** a user taps「重新填 🔄」and `taste_loaded` exists in the session
- **THEN** the system SHALL clear `taste_loaded` from the session and start the quiz from question 1
