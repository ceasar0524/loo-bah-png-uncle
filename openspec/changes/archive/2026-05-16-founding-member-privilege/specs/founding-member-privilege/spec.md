## ADDED Requirements

### Requirement: Founding member auto-marking on Lv.1 upgrade

The system SHALL mark a user as a founding member when they first upgrade to Lv.1 (「肉汁騎士」), provided: (1) the user is not the admin, and (2) the founding member counter has not yet reached 25.

The system SHALL use a Firestore transaction on `title_counter/founding_member` to atomically increment the counter and set `founding_member: true` on the user's `user_footprint` document.

The system SHALL return the member number (1–25) upon successful marking, or return (False, 0) if the limit is reached.

#### Scenario: User qualifies as founding member

- **WHEN** a non-admin user upgrades to 「肉汁騎士」 for the first time
- **AND** the founding member counter is below 25
- **THEN** the system SHALL set `founding_member: true` on the user's Firestore document
- **AND** increment the counter atomically
- **AND** return (True, N) where N is their member number

#### Scenario: Founding member limit reached

- **WHEN** a non-admin user upgrades to 「肉汁騎士」 for the first time
- **AND** the founding member counter has already reached 25
- **THEN** the system SHALL NOT set `founding_member` on the user
- **AND** return (False, 0)

#### Scenario: Admin user is excluded

- **WHEN** the admin user upgrades to 「肉汁騎士」
- **THEN** the system SHALL NOT call `_mark_founding_member`
- **AND** the counter SHALL NOT be incremented

### Requirement: Founding member skill access

The system SHALL grant founding members access to all skills up to and including Lv.3 (「魯拉（ルラ）」), regardless of their actual title level.

The system SHALL NOT grant founding members access to Lv.4 skills (「滷界敕令」/號令).

#### Scenario: Founding member uses Lv.3 skill at Lv.1

- **WHEN** a user with `founding_member: true` and title 「肉汁騎士」 triggers 「魯拉」
- **THEN** the system SHALL execute the skill as if the user has Lv.3

#### Scenario: Founding member cannot use Lv.4 skill

- **WHEN** a user with `founding_member: true` triggers 「號令」
- **AND** the user's title is below 「魯肉飯大神」
- **THEN** the system SHALL reply with the skill lock message

### Requirement: Founding member upgrade Flex Message

When a user is newly marked as a founding member during a Lv.1 upgrade, the system SHALL send an additional Flex Message immediately after the standard upgrade message.

The founding member Flex SHALL display:
- Header: 「🎖️ 封測成員特權」 and 「你是第 N 位封測成員」
- Body: 「Lv.2～3 技能全數解鎖」 followed by skill unlock descriptions for 「絕對滷域」 and 「魯拉（ルラ）」

#### Scenario: Founding member receives special Flex on upgrade

- **WHEN** a user is successfully marked as the Nth founding member during Lv.1 upgrade
- **THEN** the system SHALL append a founding member Flex Message to the upgrade reply
- **AND** the Flex SHALL display 「你是第 N 位封測成員」 with the correct member number

#### Scenario: Non-founding-member upgrade has no special Flex

- **WHEN** a user upgrades to Lv.1 but the founding member limit has been reached
- **THEN** the system SHALL send only the standard upgrade Flex Message
