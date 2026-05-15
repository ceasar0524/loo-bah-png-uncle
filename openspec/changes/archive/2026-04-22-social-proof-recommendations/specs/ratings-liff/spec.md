## ADDED Requirements

### Requirement: LIFF ratings page

The system SHALL expose a GET `/liff/ratings` Flask route that returns an HTML page suitable for display as a LINE LIFF app.

The page SHALL accept a `store` query parameter (store name) and fetch ratings from `/api/ratings/<store_name>`.

The page SHALL display the `must_eat` voter title numbers with a dynamic visual effect (implementation style — marquee, carousel, or danmaku — to be decided at implementation time).

If no must_eat votes exist, the page SHALL display「還沒有人評價，你來當第一個！」

The page SHALL include the LIFF SDK script and call `liff.init()` on load.

#### Scenario: LIFF page loaded with votes

- **WHEN** a user opens `/liff/ratings?store=<store_name>` inside LINE
- **AND** the store has `must_eat` votes
- **THEN** the page SHALL display voter title numbers with a dynamic animation effect

#### Scenario: LIFF page loaded with no votes

- **WHEN** a user opens `/liff/ratings?store=<store_name>` inside LINE
- **AND** the store has no `must_eat` votes
- **THEN** the page SHALL display「還沒有人評價，你來當第一個！」
