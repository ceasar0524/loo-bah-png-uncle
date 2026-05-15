## ADDED Requirements

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

---

### Requirement: Taste-based store matching

The system SHALL match stores from `store_notes` against the user's taste preferences using a scoring approach.

For each store with a `visual_profile`, the system SHALL compute a match score by counting how many preference dimensions the store satisfies. Each satisfied dimension adds 1 point (max 4). Dimensions where the user selected「都可以」SHALL always score 1.

The system SHALL return up to 3 stores that fully match all specified preference dimensions (score == number of questions). Stores where the user selected「都可以」for a dimension always score 1 for that dimension, effectively skipping it. Ties SHALL be broken by distance (closer is better).

If no stores fully match within the search radius, the system SHALL reply with a fallback message.

#### Scenario: Stores found matching preferences

- **WHEN** the user shares their location after completing the taste quiz
- **THEN** the system SHALL compute match scores for all stores in `store_notes` within 10 km
- **AND** return a Flex Message listing up to 3 fully matching stores sorted by distance

#### Scenario: No stores within radius or no full matches

- **WHEN** no `store_notes` stores exist within 10 km, OR no stores fully match all specified dimensions
- **THEN** the system SHALL reply with「殘念！附近剛好沒有符合的店，換個地方再試試看？」(no-match) with a LocationAction Quick Reply button「換個地方 📍」to allow the user to re-share their location, or「殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇」(no stores at all)
- **AND** the `__taste__` session SHALL remain active so the user can retry with a new location without re-filling the quiz

---

### Requirement: Taste quiz session management

The system SHALL manage quiz state per user in the existing `_sessions` dictionary using the key `taste_quiz`.

The `taste_quiz` session value SHALL store the current question index (0–3) and collected answers.

After location is received and results are sent, the system SHALL clear the `taste_quiz` session state.

#### Scenario: Session cleared after result

- **WHEN** the system sends the taste-based recommendation result
- **THEN** the `taste_quiz` session state SHALL be removed for that user
- **AND** the user's latitude and longitude SHALL be saved in the session under `last_location` for subsequent nearby hidden gems lookup

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
