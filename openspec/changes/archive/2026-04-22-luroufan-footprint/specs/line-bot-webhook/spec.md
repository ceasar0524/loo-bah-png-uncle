## ADDED Requirements

### Requirement: Footprint keyword handler

The system SHALL handle the keyword「足跡」as a top-level message trigger.

When a user sends「足跡」, the system SHALL query Firestore for that user's check-in records and reply with the footprint Flex Message.

#### Scenario: User sends 足跡

- **WHEN** a user sends the text「足跡」
- **THEN** the system SHALL read check-in records from `user_footprint/<user_id>/records/`
- **AND** reply with the footprint summary Flex Message

---

### Requirement: Check-in confirmation handler

The system SHALL handle the message「就是這家 ✅」as a check-in confirmation trigger.

The system SHALL look up the pending check-in store name stored in the user session under `pending_checkin`, write the check-in record, and clear the session state.

#### Scenario: User confirms check-in

- **WHEN** a user sends「就是這家 ✅」
- **AND** a `pending_checkin` entry exists in the user session
- **THEN** the system SHALL write the check-in record to Firestore
- **AND** clear `pending_checkin` from the session
- **AND** reply with a confirmation message

---

### Requirement: Check-in rescue handler

The system SHALL handle the message「打卡這碗 📍」as a check-in rescue trigger.

The system SHALL set a `checkin_rescue` flag in the user session and send a location request.

When the subsequent location event is received with `checkin_rescue` active, the system SHALL search nearby stores (500 m) across both databases and present them as Quick Reply buttons.

#### Scenario: User initiates check-in rescue

- **WHEN** a user sends「打卡這碗 📍」
- **THEN** the system SHALL set `checkin_rescue: true` in the session
- **AND** reply with a location request using LocationAction Quick Reply

#### Scenario: Location received during check-in rescue

- **WHEN** a location event is received
- **AND** the user session contains `checkin_rescue: true`
- **THEN** the system SHALL search `store_notes` and `hidden_gems` for stores within 500 m
- **AND** present results as Quick Reply buttons (up to 5 stores)
- **AND** clear `checkin_rescue` from the session
