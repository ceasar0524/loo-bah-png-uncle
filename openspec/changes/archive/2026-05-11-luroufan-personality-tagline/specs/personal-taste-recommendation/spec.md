## ADDED Requirements

### Requirement: Display personality tagline in taste settings

When a user views their saved taste preferences, the system SHALL compute and display a personality tagline based on their saved quiz answers using the `luroufan-personality-tagline` mapping rules.

The tagline SHALL be displayed as a separate line below the taste preference summary in the reply message.

#### Scenario: User views taste settings with saved preferences

- **WHEN** the user triggers the 查看個人口味設定 command and has saved taste preferences in Firestore
- **THEN** the system SHALL compute the personality tagline from the saved answers and include it in the reply message below the preference summary

#### Scenario: User has no saved preferences

- **WHEN** the user triggers the 查看個人口味設定 command and has no saved taste preferences
- **THEN** the system SHALL NOT display a personality tagline and SHALL prompt the user to complete the quiz
