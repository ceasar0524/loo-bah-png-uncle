## MODIFIED Requirements

### Requirement: Rich Menu buttons

The Rich Menu SHALL use a six-column layout with the following five active buttons: 怎麼用、店家清單、大叔雷達、隨機驚喜、巷子口.

#### Scenario: User taps 怎麼用

- **WHEN** the user sends the text "怎麼用"
- **THEN** the system SHALL reply with a fixed usage instruction message explaining how to send a photo to get a store identification result

#### Scenario: User taps 店家清單

- **WHEN** the user sends the text "店家清單"
- **THEN** the system SHALL reply with a dynamically generated Flex Message listing all stores in `data/store_notes.json`, grouped by district

#### Scenario: User taps 大叔雷達

- **WHEN** the user sends the text "大叔雷達"
- **THEN** the system SHALL reply with a fixed text message explaining how the radar (nearby store matching) feature works

#### Scenario: User taps 隨機驚喜

- **WHEN** the user sends the text "隨機驚喜"
- **THEN** the system SHALL enter random mode and prompt the user to share their location
- **AND** subsequent location shares SHALL trigger the random nearby store recommendation flow

#### Scenario: User taps 巷子口

- **WHEN** the user sends the text "巷子口"
- **THEN** the system SHALL reply with a Quick Reply message listing available districts from `data/hidden_gems.json`
