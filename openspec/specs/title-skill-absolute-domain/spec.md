# title-skill-absolute-domain Specification

## Purpose

TBD - created by archiving change 'title-unlock-skills'. Update Purpose after archive.

## Requirements

### Requirement: Absolute Domain map button in footprint

The system SHALL display a「絕對滷域 🗺️」button in the footprint Flex Message for users with title「滷鍋守護者」(Lv.2) or above.

For users below Lv.2, the button SHALL NOT be shown.

#### Scenario: Lv.2+ user views footprint

- **WHEN** a user with title「滷鍋守護者」or above views their footprint
- **THEN** the footprint Flex Message SHALL include a「絕對滷域 🗺️」button linking to the LIFF map page

#### Scenario: Below Lv.2 user views footprint

- **WHEN** a user with title below「滷鍋守護者」views their footprint
- **THEN** the footprint Flex Message SHALL NOT include a map button


<!-- @trace
source: title-unlock-skills
updated: 2026-05-16
code:
  - assets/rpg_map.png
  - Dockerfile
  - data/hidden_gems.json
  - data/store_hours.json
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: LIFF map page displaying checked-in stores

The system SHALL provide a LIFF page that renders a real-world map (Google Maps or Leaflet.js) showing the user's checked-in stores as location markers.

Each checked-in store SHALL be displayed as a marker on the map at its coordinate location.

Each marker SHALL have a semi-transparent circular aura representing the store's「勢力範圍」(territory). The more stores checked in, the larger the combined territory appears.

Stores not yet checked in SHALL NOT be visible on the map for Lv.2 users.

#### Scenario: User opens Absolute Domain map

- **WHEN** a Lv.2+ user taps「絕對滷域 🗺️」
- **THEN** the LIFF page SHALL open showing a map centered on the user's checked-in stores
- **AND** each checked-in store SHALL appear as a marked territory with aura

#### Scenario: User has no check-ins

- **WHEN** a Lv.2+ user opens the map but has no check-ins
- **THEN** the map SHALL display a message indicating no territories have been claimed yet

<!-- @trace
source: title-unlock-skills
updated: 2026-05-16
code:
  - assets/rpg_map.png
  - Dockerfile
  - data/hidden_gems.json
  - data/store_hours.json
  - app.py
  - .github/workflows/deploy.yml
-->