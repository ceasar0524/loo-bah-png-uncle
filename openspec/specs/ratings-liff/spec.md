# ratings-liff Specification

## Purpose

TBD - created by archiving change 'social-proof-recommendations'. Update Purpose after archive.

## Requirements

### Requirement: LIFF ratings page

The system SHALL expose a GET `/liff/ratings` Flask route that returns an HTML page suitable for display as a LINE LIFF app.

The page SHALL accept a `store` query parameter (store name) and fetch ratings from `/api/ratings/<store_name>`.

The page SHALL display all voter title numbers (all rating types) as a danmaku animation.

Each danmaku item SHALL include the voter's current title (real-time, not title at rating time) and a label describing their rating:
- `must_eat` → 「說必吃！🔥」
- `neutral` → 「說普通 😐」
- `bad` → 「說不能只有我吃到 🤫」

If no votes exist, the page SHALL display「還沒有人評價，你來當第一個！」

The page SHALL include the LIFF SDK script and call `liff.init()` on load.

The `/api/ratings/<store_name>` endpoint SHALL return all votes (not just `must_eat`), each formatted as `{title}#{title_number} {label}`, sorted by title rank (highest first). The voter's title SHALL be looked up in real time from `user_footprint/<user_id>` rather than the stored title at rating time.

#### Scenario: LIFF page loaded with votes

- **WHEN** a user opens `/liff/ratings?store=<store_name>` inside LINE
- **AND** the store has any votes
- **THEN** the page SHALL display voter title numbers with rating labels as danmaku

#### Scenario: LIFF page loaded with no votes

- **WHEN** a user opens `/liff/ratings?store=<store_name>` inside LINE
- **AND** the store has no votes
- **THEN** the page SHALL display「還沒有人評價，你來當第一個！」

<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->