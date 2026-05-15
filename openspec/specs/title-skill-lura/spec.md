# title-skill-lura Specification

## Purpose

TBD - created by archiving change 'title-unlock-skills'. Update Purpose after archive.

## Requirements

### Requirement: Lura skill activation

The system SHALL provide a skill called「魯拉（ルラ）」unlocked at Lv.3 (「魯肉飯勇者」or above).

When a user with Lv.3+ title sends the text「魯拉」, the system SHALL reply with「🌀 魯拉發動！」and present three Quick Reply options:
-「🍚 最近攻略」— most recently checked-in stores
-「🍚 最常回訪」— stores with the highest visit count
-「🍚 好久沒吃」— stores not visited for the longest time

#### Scenario: User sends 魯拉 at Lv.3+

- **WHEN** a user with title「魯肉飯勇者」or above sends the text「魯拉」
- **THEN** the system SHALL reply with「🌀 魯拉發動！」
- **AND** display Quick Reply buttons:「🍚 最近攻略」「🍚 最常回訪」「🍚 好久沒吃」

#### Scenario: User sends 魯拉 below Lv.3

- **WHEN** a user with title below「魯肉飯勇者」sends the text「魯拉」
- **THEN** the system SHALL NOT trigger the Lura skill
- **AND** the system SHALL reply with a message indicating the skill is not yet unlocked


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
### Requirement: Lura store list by category

After the user selects a category, the system SHALL display a list of the user's checked-in stores matching that category. Each store in the list SHALL include a Google Maps navigation button.

The list SHALL show up to 5 stores per category.

#### Scenario: User selects 最近攻略

- **WHEN** the user taps「🍚 最近攻略」
- **THEN** the system SHALL display the user's most recently checked-in stores
- **AND** each store SHALL have a「前往導航 🗺️」button that opens Google Maps navigation

#### Scenario: User selects 最常回訪

- **WHEN** the user taps「🍚 最常回訪」
- **THEN** the system SHALL display the user's stores with the highest visit count
- **AND** each store SHALL have a「前往導航 🗺️」button that opens Google Maps navigation

#### Scenario: User selects 好久沒吃

- **WHEN** the user taps「🍚 好久沒吃」
- **THEN** the system SHALL display the user's stores not visited for the longest time
- **AND** each store SHALL have a「前往導航 🗺️」button that opens Google Maps navigation


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
### Requirement: Google Maps navigation link

Each store navigation button SHALL open Google Maps with the store's coordinates as the destination.

#### Scenario: User taps navigation button

- **WHEN** the user taps「前往導航 🗺️」for a store
- **THEN** the system SHALL open Google Maps with that store's latitude and longitude as the destination

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