## ADDED Requirements

### Requirement: Social proof LIFF button and weight boost in random recommendation

The random nearby recommendation SHALL apply rating weight boost and include a LIFF ratings button.

#### Scenario: Random draw applies rating weights

- **WHEN** the system draws a random store from nearby candidates
- **THEN** stores with `must_eat` votes SHALL have weight = min(1.0 + votes × 0.5, 3.0)
- **AND** stores without votes SHALL have weight = 1.0

#### Scenario: Random recommendation Flex Message includes LIFF button

- **WHEN** the random recommendation Flex Message is built
- **THEN** the system SHALL include a「查看評價 💬」URIAction button linking to the LIFF ratings page for that store
