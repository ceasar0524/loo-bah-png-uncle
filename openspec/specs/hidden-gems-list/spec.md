# hidden-gems-list Specification

## Purpose

TBD - created by archiving change 'hidden-gems-list'. Update Purpose after archive.

## Requirements

### Requirement: Hidden gems list trigger

The system SHALL respond to the text "巷子口" by sending a Quick Reply message listing all districts that have at least one store in `data/hidden_gems.json`.

#### Scenario: User sends 巷子口

- **WHEN** the user sends the text "巷子口"
- **THEN** the system SHALL reply with a text message and Quick Reply buttons, one button per district found in `hidden_gems.json`

#### Scenario: No stores in hidden gems

- **WHEN** `hidden_gems.json` is empty
- **THEN** the system SHALL reply with a text message indicating no stores are available yet


<!-- @trace
source: hidden-gems-list
updated: 2026-04-14
code:
  - app.py
  - data/hidden_gems.json
-->

---
### Requirement: Hidden gems district store list

The system SHALL respond to a district name Quick Reply selection by returning a Flex Message listing all stores in that district from `data/hidden_gems.json`.

Each store entry SHALL include the store name and a map button linking to `https://maps.google.com/?q=<lat>,<lng>`.

The Flex Message SHALL include a footer note: "名單持續擴充中，歡迎推薦！"

#### Scenario: User selects a district

- **WHEN** the user sends a district name that matches a key in `hidden_gems.json`
- **THEN** the system SHALL reply with a Flex Message listing all stores in that district, each with a Google Maps button

#### Scenario: District has no stores

- **WHEN** the user sends a district name with no matching stores
- **THEN** the system SHALL reply with a message indicating no stores are found in that district


<!-- @trace
source: hidden-gems-list
updated: 2026-04-14
code:
  - app.py
  - data/hidden_gems.json
-->

---
### Requirement: Hidden gems data source

The system SHALL load `data/hidden_gems.json` at startup. Each entry SHALL have the store name as key and a `location` object with `lat` and `lng` fields.

District grouping SHALL be derived from the store name by extracting the text inside parentheses, e.g., "路路食堂（林口區）" → "林口區".

#### Scenario: Data loaded at startup

- **WHEN** the application starts
- **THEN** `hidden_gems.json` SHALL be loaded into memory alongside `store_notes.json`

#### Scenario: District extraction from store name

- **WHEN** a store name contains text in fullwidth parentheses （）
- **THEN** the system SHALL extract the content as the district label for grouping and Quick Reply

<!-- @trace
source: hidden-gems-list
updated: 2026-04-14
code:
  - app.py
  - data/hidden_gems.json
-->

---
### Requirement: Social proof LIFF button in hidden gems list

The hidden gems list Flex Message SHALL include a「查看評價 💬」LIFF button for each listed store.

#### Scenario: Hidden gems list includes LIFF button

- **WHEN** the hidden gems list Flex Message is built for a store
- **THEN** the system SHALL include a「查看評價 💬」URIAction button linking to the LIFF ratings page for that store

<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->