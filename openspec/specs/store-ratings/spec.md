# store-ratings Specification

## Purpose

TBD - created by archiving change 'social-proof-recommendations'. Update Purpose after archive.

## Requirements

### Requirement: Rating prompt after check-in

After a check-in confirmation is sent, the system SHALL send a rating invitation as a separate message with three Quick Reply buttons:「必吃 👍」、「普通 😐」、「不能只有我吃到 🤫」.

The rating invitation SHALL store the pending store name in session under `pending_rating`.

#### Scenario: Rating prompt sent after check-in

- **WHEN** a check-in confirmation is sent to the user
- **AND** a title upgrade ceremony is NOT triggered
- **THEN** the system SHALL send a rating invitation message with three Quick Reply options
- **AND** store the checked-in store name in session `pending_rating`

#### Scenario: Rating prompt sent after upgrade ceremony

- **WHEN** a check-in confirmation and title upgrade ceremony are both sent
- **THEN** the system SHALL send the rating invitation after the upgrade ceremony message


<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->

---
### Requirement: Rating storage

The system SHALL handle the three rating Quick Reply messages and write the result to Firestore.

「必吃 👍」SHALL be stored as `must_eat`. 「普通 😐」SHALL be stored as `neutral`. 「不能只有我吃到 🤫」is a negative rating (too bad to eat alone — dragging friends to suffer) and SHALL be stored as `bad`.

Each user SHALL have at most one rating per store. Repeated ratings SHALL overwrite the previous value.

The write SHALL be performed asynchronously in a background thread.

#### Scenario: User taps 必吃

- **WHEN** a user taps「必吃 👍」
- **AND** a `pending_rating` exists in session
- **THEN** the system SHALL write `rating: "must_eat"` to `store_ratings/<store_name>/votes/<user_id>`
- **AND** include the user's current `title` and `title_number` in the record
- **AND** clear `pending_rating` from session

#### Scenario: User taps 不能只有我吃到

- **WHEN** a user taps「不能只有我吃到 🤫」
- **AND** a `pending_rating` exists in session
- **THEN** the system SHALL write `rating: "bad"` to `store_ratings/<store_name>/votes/<user_id>`
- **AND** include the user's current `title` and `title_number` in the record
- **AND** clear `pending_rating` from session

#### Scenario: User taps 普通

- **WHEN** a user taps「普通 😐」
- **AND** a `pending_rating` exists in session
- **THEN** the system SHALL write `rating: "neutral"` to `store_ratings/<store_name>/votes/<user_id>`
- **AND** clear `pending_rating` from session


<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->

---
### Requirement: Social proof LIFF button in recommendations

When building a recommendation Flex Message for any store, the system SHALL include a「查看評價 💬」button as a URIAction linking to `/liff/ratings?store=<store_name>`.

The button SHALL always appear regardless of whether the store has any ratings.

#### Scenario: Recommendation Flex Message includes LIFF button

- **WHEN** a recommendation Flex Message is built for a store
- **THEN** the system SHALL include a「查看評價 💬」URIAction button pointing to the ratings LIFF page for that store


<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->

---
### Requirement: Ratings API endpoint

The system SHALL expose a GET `/api/ratings/<store_name>` endpoint that returns all voter entries for the given store, sorted by title rank (highest first).

Each entry SHALL be formatted as `"{title}#{title_number} {label}"` where label is:
- `must_eat` → 「說必吃！🔥」
- `neutral` → 「說普通 😐」
- `bad` → 「說不能只有我吃到 🤫」

The voter's current title SHALL be looked up in real time from `user_footprint/<user_id>`, falling back to the stored title if the user document does not exist.

The response SHALL be JSON: `{ "votes": ["魯肉飯勇者#12 說必吃！🔥", "肉汁騎士#33 說普通 😐"] }`.

If no votes exist, `votes` SHALL be an empty array.

#### Scenario: Ratings API returns votes

- **WHEN** a GET request is made to `/api/ratings/<store_name>`
- **AND** the store has votes in Firestore
- **THEN** the system SHALL return a JSON response with all voter entries sorted by title rank

#### Scenario: Ratings API returns empty

- **WHEN** a GET request is made to `/api/ratings/<store_name>`
- **AND** the store has no votes
- **THEN** the system SHALL return `{ "votes": [] }`


<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->

---
---
### Requirement: Social proof count in store lists

The system SHALL display「N 位同好推薦 🔥」below the store name in:
- The store list (店家清單, all 24 `store_notes` stores)
- The 巷仔口 district lists (all districts including 台北市區)

The count SHALL reflect the number of `must_eat` votes in Firestore, queried at render time.

The label SHALL only appear when count > 0.

#### Scenario: Store has must_eat votes in list

- **WHEN** a store list or 巷仔口 list is rendered
- **AND** a store has one or more `must_eat` votes
- **THEN** the system SHALL display「N 位同好推薦 🔥」below the store name

---
### Requirement: Rating weight boost for random recommendation

Stores with `must_eat` votes SHALL receive a weight boost in the random nearby recommendation draw.

The base weight for each store SHALL be 1.0. Each `must_eat` vote SHALL add 0.5 to the weight, with a maximum weight of 3.0.

#### Scenario: Store has must_eat votes in random draw

- **WHEN** the random nearby recommendation draws from nearby stores
- **THEN** stores with `must_eat` votes SHALL have weight = min(1.0 + votes × 0.5, 3.0)
- **AND** stores without votes SHALL have weight = 1.0

<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->