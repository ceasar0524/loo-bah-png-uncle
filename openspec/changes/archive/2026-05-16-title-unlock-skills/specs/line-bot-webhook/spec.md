## ADDED Requirements

### Requirement: 肉盾 text trigger

The system SHALL handle the text「肉盾」as a skill trigger for users with title「肉汁騎士」or above.

#### Scenario: 肉盾 trigger with sufficient title

- **WHEN** a user with Lv.1+ title sends the text「肉盾」
- **THEN** the system SHALL enter the meat shield evaluation flow as defined in `title-skill-meat-shield`

#### Scenario: 肉盾 trigger with insufficient title

- **WHEN** a user with title「無職轉生者」sends the text「肉盾」
- **THEN** the system SHALL reply indicating the skill has not been unlocked yet

### Requirement: 魯拉 text trigger

The system SHALL handle the text「魯拉」as a skill trigger for users with title「魯肉飯勇者」or above.

#### Scenario: 魯拉 trigger with sufficient title

- **WHEN** a user with Lv.3+ title sends the text「魯拉」
- **THEN** the system SHALL enter the Lura navigation flow as defined in `title-skill-lura`

#### Scenario: 魯拉 trigger with insufficient title

- **WHEN** a user with title below「魯肉飯勇者」sends the text「魯拉」
- **THEN** the system SHALL reply indicating the skill has not been unlocked yet

### Requirement: 號令 text trigger

The system SHALL handle the text「號令」as a skill trigger.

For users with title「魯肉飯大神」, the system SHALL enter the decree posting flow.

For all other users, the system SHALL display the Decree Wall (today's recommendations).

#### Scenario: 號令 trigger for 大神 user

- **WHEN** a user with title「魯肉飯大神」sends the text「號令」
- **THEN** the system SHALL enter the decree posting flow as defined in `title-skill-decree`

#### Scenario: 號令 trigger for non-大神 user

- **WHEN** a user with title below「魯肉飯大神」sends the text「號令」
- **THEN** the system SHALL display the Decree Wall
