## ADDED Requirements

### Requirement: Absolute Domain button in footprint Flex Message

The footprint Flex Message SHALL include a「絕對滷域 🗺️」button for users with title「滷鍋守護者」(Lv.2) or above. The button SHALL open the Absolute Domain LIFF map page.

For users with title below Lv.2, the button SHALL NOT be rendered.

#### Scenario: Lv.2+ user footprint includes map button

- **WHEN** `_build_footprint_flex` is called for a user with title「滷鍋守護者」or above
- **THEN** the returned Flex Message SHALL include a「絕對滷域 🗺️」URI button
- **AND** the button URI SHALL point to the Absolute Domain LIFF URL

#### Scenario: Below Lv.2 user footprint excludes map button

- **WHEN** `_build_footprint_flex` is called for a user with title below「滷鍋守護者」
- **THEN** the returned Flex Message SHALL NOT include the map button
