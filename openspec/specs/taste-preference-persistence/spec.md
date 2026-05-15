# taste-preference-persistence Specification

## Purpose

TBD - created by archiving change 'save-taste-preference'. Update Purpose after archive.

## Requirements

### Requirement: Save taste preferences to Firestore

The system SHALL save user taste preferences to Firestore collection `user_preferences` with the document ID set to the LINE `user_id`.

The document SHALL contain a `taste` field with the four preference values (`fat_ratio`, `skin`, `sauce_consistency`, `sauce_taste`) and an `updated_at` timestamp.

Write operations SHALL be performed asynchronously in a background thread to avoid blocking the webhook response.

#### Scenario: User confirms save

- **WHEN** a user taps「儲存 ✅」after completing the taste quiz
- **THEN** the system SHALL write the preference answers to Firestore under `user_preferences/<user_id>`
- **AND** clear the pending save state from the session
- **AND** proceed to ask for the user's location

#### Scenario: User declines save

- **WHEN** a user taps「不用 ❌」after completing the taste quiz
- **THEN** the system SHALL NOT write to Firestore
- **AND** clear the pending save state from the session
- **AND** proceed to ask for the user's location


<!-- @trace
source: save-taste-preference
updated: 2026-04-19
code:
  - app.py
-->

---
### Requirement: Load saved taste preferences

The system SHALL read saved preferences from Firestore when the user triggers「個人化」.

If preferences exist, the system SHALL display a Flex Message summarizing the saved preferences and offer Quick Reply options「直接用 ✅」and「重新填 🔄」.

The Flex Message SHALL have a dark header「🍚 大叔記得你的口味」and list each preference dimension on a separate centered line using an emoji icon and the human-readable value (e.g., 🍖 偏瘦, 💋 不黏, 🍯 不稠, 🧂 偏鹹).

#### Scenario: Preferences found on trigger

- **WHEN** a user sends「個人化」
- **AND** a saved preference document exists in Firestore for that user
- **THEN** the system SHALL display the preference summary and Quick Reply buttons「直接用 ✅」/「重新填 🔄」

#### Scenario: No preferences found on trigger

- **WHEN** a user sends「個人化」
- **AND** no saved preference document exists in Firestore for that user
- **THEN** the system SHALL start the taste quiz from question 1


<!-- @trace
source: save-taste-preference
updated: 2026-04-19
code:
  - app.py
-->

---
### Requirement: Apply saved preferences directly

The system SHALL allow users to skip the quiz and use their saved preferences directly.

#### Scenario: User chooses to reuse saved preferences

- **WHEN** a user taps「直接用 ✅」
- **THEN** the system SHALL load the saved preferences into the session
- **AND** set the session store to `__taste__`
- **AND** prompt the user to share their location


<!-- @trace
source: save-taste-preference
updated: 2026-04-19
code:
  - app.py
-->

---
### Requirement: Overwrite saved preferences

When a user chooses「重新填 🔄」and completes the quiz, the system SHALL ask again whether to save (overwriting the previous record).

#### Scenario: User re-fills and saves

- **WHEN** a user taps「重新填 🔄」, completes all four questions, and then taps「儲存 ✅」
- **THEN** the system SHALL overwrite the existing Firestore document with the new answers

#### Scenario: User re-fills and declines save

- **WHEN** a user taps「重新填 🔄」, completes all four questions, and then taps「不用 ❌」
- **THEN** the system SHALL NOT update the existing Firestore document

<!-- @trace
source: save-taste-preference
updated: 2026-04-19
code:
  - app.py
-->