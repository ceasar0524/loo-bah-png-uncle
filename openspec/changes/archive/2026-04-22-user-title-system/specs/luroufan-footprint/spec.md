## ADDED Requirements

### Requirement: Footprint query

The system SHALL allow users to query their footprint by sending the keyword「足跡」.

The system SHALL reply with a Flex Message showing:
- Current title and title number (e.g., 老饕#47)
- Total unique stores checked in (out of 96)
- Most recent check-in store name and date
- List of checked-in stores, up to 10, sorted by most recent first

#### Scenario: User queries footprint with records

- **WHEN** a user sends「足跡」
- **AND** the user has at least one check-in record in Firestore
- **THEN** the system SHALL reply with a Flex Message that includes the user's title, title number, unique store count, most recent check-in, and store list

#### Scenario: User queries footprint with no records

- **WHEN** a user sends「足跡」
- **AND** the user has no check-in records
- **THEN** the system SHALL reply with a message encouraging the user to take a photo and start checking in
