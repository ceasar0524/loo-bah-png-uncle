## ADDED Requirements

### Requirement: Random surprise trigger via text keyword

The system SHALL handle the text keyword「隨機驚喜」in `handle_text`. Upon receiving this keyword, the system SHALL:
1. Reply with a prompt message asking the user to share their location
2. Store the special session value `"__random__"` for that user

#### Scenario: User sends 隨機驚喜

- **WHEN** a LINE user sends the text message「隨機驚喜」
- **THEN** the system SHALL reply with a location-request Quick Reply message and store `"__random__"` in the user's session

## MODIFIED Requirements

### Requirement: Handle location message

The system SHALL handle LINE location message events. Upon receiving a location message, the system SHALL retrieve the stored session value for that user and branch based on the value:

- If the session value is `"__random__"`: run `search_random_nearby_store` and send the uncle persona's `generate_random` response
- If the session value is a store name: run `search_nearby_stores` and send the uncle persona's `generate_nearby` response

#### Scenario: Location received with valid session (style match)

- **WHEN** a location message is received and the session contains a store name (not `"__random__"`)
- **THEN** the system SHALL run nearby store search and return the uncle persona recommendation response

#### Scenario: Location received with random surprise session

- **WHEN** a location message is received and the session value is `"__random__"`
- **THEN** the system SHALL run `search_random_nearby_store` and return the uncle persona `generate_random` response

#### Scenario: Location received with expired session

- **WHEN** a location message is received but no session exists for that user
- **THEN** the system SHALL respond asking the user to send a photo first
