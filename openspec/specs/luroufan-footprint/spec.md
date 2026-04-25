# luroufan-footprint Specification

## Purpose

TBD - created by archiving change 'luroufan-footprint'. Update Purpose after archive.

## Requirements

### Requirement: Check-in after successful photo recognition

After a successful photo recognition result (single store identified with high confidence and `is_lu_rou_fan` is true), the system SHALL display two Quick Reply buttons alongside the existing response:
- `✅ {store_name}` — confirms the identified store is correct
- 「打卡這碗 📍」— allows the user to correct the store via location if recognition is wrong

When the user taps `✅ {store_name}`, the system SHALL record a check-in entry for that store in Firestore under `user_footprint/<user_id>/records/`.

When the user taps「打卡這碗 📍」, the system SHALL clear the pending check-in session and enter the location-based rescue flow.

The button label `✅ {store_name}` SHALL display the identified store name so the user can verify the recognition result before confirming.

#### Scenario: User confirms check-in after recognition

- **WHEN** photo recognition identifies a store with high confidence
- **AND** the user taps `✅ {store_name}`
- **THEN** the system SHALL write a check-in record to Firestore with `store_name`, `db` source, and `checked_in_at` timestamp
- **AND** reply with a confirmation message from the uncle

#### Scenario: User corrects wrong recognition

- **WHEN** photo recognition identifies a store with high confidence
- **AND** the user taps「打卡這碗 📍」instead
- **THEN** the system SHALL clear the pending check-in session and enter the location-based rescue flow

#### Scenario: User does not confirm check-in

- **WHEN** photo recognition identifies a store
- **AND** the user does not tap either button
- **THEN** no check-in record SHALL be created


<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Check-in rescue via location when recognition fails

When photo recognition results in a tie or complete failure (no store identified), AND the image is identified as lu_rou_fan (`is_lu_rou_fan` is true), the system SHALL display a Quick Reply button「打卡這碗 📍」alongside the existing response.

When the image is NOT lu_rou_fan, no check-in button SHALL be displayed.

When the user taps「打卡這碗 📍」, the system SHALL request the user's location. Upon receiving the location, the system SHALL search both `store_notes` and `hidden_gems` databases for stores within 500 metres and present them as Quick Reply buttons for the user to select. An additional escape option「找不到我吃的店 🤷」SHALL always be included as the last Quick Reply item.

#### Scenario: User initiates location-based check-in

- **WHEN** photo recognition results in a tie or failure for a lu_rou_fan image
- **AND** the user taps「打卡這碗 📍」
- **THEN** the system SHALL send a location request message with a LocationAction Quick Reply

#### Scenario: Nearby stores found

- **WHEN** the user shares their location for check-in rescue
- **AND** one or more stores exist within 500 metres across both databases
- **THEN** the system SHALL list stores as Quick Reply buttons (store name, up to 5)
- **AND** append「找不到我吃的店 🤷」as the final option
- **AND** the user tapping a store name SHALL trigger a check-in record for that store

#### Scenario: User taps escape option

- **WHEN** the user taps「找不到我吃的店 🤷」
- **THEN** the system SHALL clear the rescue session state
- **AND** reply「拍謝！這家大叔還不認識，下次再來！」

#### Scenario: No nearby stores found

- **WHEN** the user shares their location for check-in rescue
- **AND** no stores exist within 500 metres
- **THEN** the system SHALL reply indicating no nearby stores and clear the pending check-in session state


<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Footprint query

The system SHALL allow users to query their footprint by sending the keyword「足跡」.

The system SHALL reply with a Flex Message showing:
- Header (dark brown background):
  - Total unique stores checked in (out of 96) in large gold text
  - Current title and title number (e.g. `肉汁騎士#1-a3f9`) in small gold text
  - Uncle certification phrase for current title in pale gold small text
- Body (cream background):
  - Upgrade progress prompt if not at maximum title (orange-brown bold text)
  - Most recent check-in store name and date
  - List of checked-in stores, up to 10, sorted by most recent first; each store row includes a heart toggle button (❤️ if favorited, 🤍 if not)
  - If more than 10 stores, the response SHALL be a Flex Carousel with a second bubble showing the remaining stores, also with heart toggle buttons

#### Scenario: User queries footprint with records

- **WHEN** a user sends「足跡」
- **AND** the user has at least one check-in record in Firestore
- **THEN** the system SHALL reply with a Flex Message (or Carousel if >10 stores) summarising the user's footprint including title and upgrade progress

#### Scenario: User queries footprint with no records

- **WHEN** a user sends「足跡」
- **AND** the user has no check-in records
- **THEN** the system SHALL reply with a message encouraging the user to take a photo and start checking in


<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->


<!-- @trace
source: user-title-system
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Firestore check-in storage

The system SHALL store check-in records in Firestore collection `user_footprint` with sub-collection `records`.

Each record document SHALL contain:
- `store_name`: string — the checked-in store name
- `db`: string — `"store_notes"` or `"hidden_gems"`
- `checked_in_at`: Firestore timestamp

The same store MAY be checked in multiple times. Footprint queries SHALL deduplicate by `store_name` when counting unique stores visited.

Firestore writes SHALL be performed asynchronously in a background thread to avoid blocking the webhook response.

#### Scenario: Check-in record written

- **WHEN** a user confirms a check-in
- **THEN** the system SHALL write a record to `user_footprint/<user_id>/records/<auto_id>` asynchronously
- **AND** the webhook response SHALL not be delayed by the write operation

#### Scenario: Duplicate check-in

- **WHEN** a user checks in to a store they have previously visited
- **THEN** a new record SHALL be created (preserving full visit history)
- **AND** footprint query SHALL count that store only once toward the unique total


<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
---
### Requirement: Favorite store (愛店)

The system SHALL allow users to mark checked-in stores as favorites via a heart toggle button in the footprint Flex Message.

Each store row in the footprint SHALL display a heart button: ❤️ if the store is in the user's favorites, 🤍 if not.

Tapping the heart button SHALL trigger a Postback event with `data="fav:<store_name>"`.

The system SHALL toggle the store's presence in the `favorites` list field of `user_footprint/<user_id>` (add if absent, remove if present).

After toggling, the system SHALL reply with an updated footprint Flex Message reflecting the new favorite state.

Favorites SHALL be stored as an array in the `user_footprint/<user_id>` document under the field `favorites`.

#### Scenario: User favorites a store

- **WHEN** a user taps 🤍 next to a store in the footprint
- **THEN** the system SHALL add the store to `favorites` in Firestore
- **AND** reply with an updated footprint Flex Message showing ❤️ for that store

#### Scenario: User unfavorites a store

- **WHEN** a user taps ❤️ next to a store in the footprint
- **THEN** the system SHALL remove the store from `favorites` in Firestore
- **AND** reply with an updated footprint Flex Message showing 🤍 for that store

---
### Requirement: CHECKIN_ENABLED feature flag

All check-in related functionality (Quick Reply buttons, handlers, footprint query) SHALL be gated behind the `CHECKIN_ENABLED` environment variable (default: `true`). When set to `false`, no check-in buttons SHALL be displayed and check-in keyword handlers SHALL be inactive.

<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->