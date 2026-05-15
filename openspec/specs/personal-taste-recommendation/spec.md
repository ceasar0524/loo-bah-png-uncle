# personal-taste-recommendation Specification

## Purpose

TBD - created by archiving change 'personal-recommendation'. Update Purpose after archive.

## Requirements

### Requirement: Taste preference quiz

The system SHALL collect user taste preferences through a four-question Quick Reply quiz triggered by the keyword「個人化」.

Each question SHALL be sent as a separate message with Quick Reply buttons. The questions SHALL be asked in this order:

1. **肉質偏好**: 偏肥 / 偏瘦 / 都可以 → maps to `visual_profile.fat_ratio`
2. **喜歡黏一點**: 黏黏 / 不黏 / 都可以 → maps to `visual_profile.skin` (with_skin / without_skin)
3. **滷汁濃稠**: 稠 / 不稠 / 都可以 → maps to top-level `sauce_consistency` (稠/水)
4. **口味偏好**: 偏甜（南部）/ 偏鹹（北部）/ 都可以 → maps to `visual_profile.sauce_taste`

The system SHALL store answers in the user session under a `taste_quiz` state.

After the fourth question is answered, the system SHALL prompt the user to share their location.

#### Scenario: User triggers personal recommendation

- **WHEN** a user sends「個人化」
- **THEN** the system SHALL reply with the first quiz question and Quick Reply buttons, and store the quiz state in the session

#### Scenario: User answers each quiz question

- **WHEN** the user taps a Quick Reply button during the taste quiz
- **THEN** the system SHALL store the answer and send the next question
- **AND** after the fourth answer the system SHALL prompt the user to share their location

#### Scenario: User selects 都可以

- **WHEN** the user selects「都可以」for any dimension
- **THEN** the system SHALL treat that dimension as unfiltered (matches all stores)


<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: Taste-based store matching

The system SHALL match stores from `store_notes` against the user's taste preferences using a scoring approach.

For each store with a `visual_profile`, the system SHALL compute a match score by counting how many preference dimensions the store satisfies. Each satisfied dimension adds 1 point (max 4). Dimensions where the user selected「都可以」SHALL always score 1.

The system SHALL prioritize stores that fully match all specified preference dimensions (score == number of questions), returning up to 3. Ties SHALL be broken by distance (closer is better).

If no stores fully match, the system SHALL fall back to stores with score == (number of questions - 1), returning up to 2. These partial-match stores SHALL be labeled「差一點點，可以考慮」in the Flex Message.

If neither full nor partial matches exist, the system SHALL reply with a fallback message.

#### Scenario: Stores found matching preferences (full match)

- **WHEN** the user shares their location after completing the taste quiz
- **THEN** the system SHALL compute match scores for all stores in `store_notes` within 10 km
- **AND** return a Flex Message listing up to 3 fully matching stores sorted by distance

#### Scenario: No full matches, partial matches found

- **WHEN** no stores fully match all preference dimensions
- **AND** stores with score == (number of questions - 1) exist within 10 km
- **THEN** the system SHALL return a Flex Message listing up to 2 partial-match stores
- **AND** each partial-match store SHALL be labeled「很接近，可以考慮」below the store name

#### Scenario: Recommended store is currently closed

- **WHEN** a recommended store's opening hours in `store_hours.json` indicate it is currently closed
- **THEN** the store name SHALL have「（目前打烊）」appended, the name text SHALL be grayed (`#AAAAAA`), and the map button SHALL use secondary style
- **WHEN** a store has no hours data in `store_hours.json`
- **THEN** the store SHALL be treated as open

#### Scenario: No stores within radius or no matches at all

- **WHEN** no `store_notes` stores exist within 10 km, OR neither full nor partial matches exist
- **THEN** the system SHALL reply with「殘念！附近剛好沒有符合的店，換個地方再試試看？」(no-match) with a LocationAction Quick Reply button「換個地方 📍」to allow the user to re-share their location, or「殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇」(no stores at all)
- **AND** the `__taste__` session SHALL remain active so the user can retry with a new location without re-filling the quiz


<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: Taste quiz session management

The system SHALL manage quiz state per user in the existing `_sessions` dictionary using the key `taste_quiz`.

The `taste_quiz` session value SHALL store the current question index (0–3) and collected answers.

After location is received and results are sent, the system SHALL clear the `taste_quiz` session state.

#### Scenario: Session cleared after result

- **WHEN** the system sends the taste-based recommendation result
- **THEN** the `taste_quiz` session state SHALL be removed for that user
- **AND** the user's latitude and longitude SHALL be saved in the session under `last_location` for subsequent nearby hidden gems lookup


<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: Nearby hidden gems listing after taste recommendation

After receiving personal recommendation results, the system SHALL display a Quick Reply button「附近巷仔口 🏘️」at the bottom of the Flex Message.

When the user taps this button, the system SHALL use the saved `last_location` to find hidden gems stores within 3 km, sorted by distance, and return up to 3 stores.

If a store's business hours are available in `store_hours.json`, the system SHALL check whether the store is currently open. Closed stores SHALL still be listed but SHALL be visually distinguished with the label「（目前打烊）」and a secondary button style.

If no hidden gems stores are found within 3 km, the system SHALL reply with a message indicating no nearby stores are available.

After the nearby hidden gems result is sent, the system SHALL clear `last_location` from the session.

The Quick Reply button SHALL send the text「附近巷仔口店家」(not「巷仔口」) to avoid conflict with the rich menu keyword.

#### Scenario: User taps 附近巷仔口 after personal recommendation

- **WHEN** the user taps「附近巷仔口 🏘️」after receiving personal recommendation results (sends「附近巷仔口店家」)
- **AND** a `last_location` exists in the session
- **THEN** the system SHALL return a Flex Message listing up to 3 hidden gems stores within 3 km, with open/closed status indicated

#### Scenario: No hidden gems within 3 km

- **WHEN** no hidden gems stores are found within 3 km of the saved location
- **THEN** the system SHALL reply with「殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇」

#### Scenario: Store is closed

- **WHEN** a nearby hidden gems store is currently outside its business hours
- **THEN** the store SHALL be listed with「（目前打烊）」appended to its name, grayed text, and secondary map button style

<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: Social proof LIFF button in personal taste recommendation

The personal taste recommendation Flex Message SHALL include a「查看評價 💬」LIFF button for each recommended store.

#### Scenario: Personal recommendation includes LIFF button

- **WHEN** the personal taste recommendation Flex Message is built for a store
- **THEN** the system SHALL include a「查看評價 💬」URIAction button linking to the LIFF ratings page for that store

<!-- @trace
source: social-proof-recommendations
updated: 2026-04-22
code:
  - app.py
  - .github/workflows/deploy.yml
  - src/pipeline.py
-->

---
### Requirement: Photo recognition response includes check-in entry point

The system SHALL include a check-in Quick Reply button in the photo recognition response, depending on the recognition outcome.

When recognition identifies a single store with high confidence, the system SHALL:
1. Store the identified store name in the user session under `pending_checkin`
2. Append a Quick Reply button「就是這家 ✅」to the response

When recognition results in a tie or complete failure, the system SHALL:
1. Append a Quick Reply button「打卡這碗 📍」to the response

#### Scenario: High-confidence recognition — check-in button appended

- **WHEN** photo recognition identifies a store with high confidence
- **THEN** the system SHALL store the store name in session `pending_checkin`
- **AND** include「就是這家 ✅」as a Quick Reply button alongside existing Quick Reply options

#### Scenario: Tie or failure recognition — rescue button appended

- **WHEN** photo recognition results in a tie or complete failure
- **THEN** the system SHALL include「打卡這碗 📍」as a Quick Reply button alongside existing Quick Reply options

<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Display personality tagline in taste settings

When a user views their saved taste preferences, the system SHALL compute and display a personality tagline based on their saved quiz answers using the `luroufan-personality-tagline` mapping rules.

The tagline SHALL be displayed as a separate line below the taste preference summary in the reply message.

#### Scenario: User views taste settings with saved preferences

- **WHEN** the user triggers the 查看個人口味設定 command and has saved taste preferences in Firestore
- **THEN** the system SHALL compute the personality tagline from the saved answers and include it in the reply message below the preference summary

#### Scenario: User has no saved preferences

- **WHEN** the user triggers the 查看個人口味設定 command and has no saved taste preferences
- **THEN** the system SHALL NOT display a personality tagline and SHALL prompt the user to complete the quiz

<!-- @trace
source: luroufan-personality-tagline
updated: 2026-05-11
code:
  - .github/workflows/deploy.yml
  - app.py
-->
---
### Requirement: Share taste profile

The 查看個人口味設定 Flex Message SHALL include a「分享口味 📤」Quick Reply button that opens the `/liff/share-taste` LIFF page.

The share URL SHALL include the personality tagline text, hero image URL, and all four taste dimension labels as query parameters.

The `/liff/share-taste` LIFF page SHALL use `liff.shareTargetPicker` to send a Flex Message containing the hero image, tagline in the header, four taste dimension rows in the body, and a「加入魯肉飯大叔」button.

#### Scenario: User shares taste profile

- **WHEN** the user taps「分享口味 📤」from the 查看個人口味設定 reply
- **THEN** the LIFF page SHALL open and immediately invoke `liff.shareTargetPicker`
- **AND** the shared Flex Message SHALL display the hero image, tagline, and all four taste dimensions
- **AND** include a「🤖 加入魯肉飯大叔」button

<!-- @trace
source: share-taste-profile
updated: 2026-05-11
code:
  - app.py
  - .github/workflows/deploy.yml
-->
