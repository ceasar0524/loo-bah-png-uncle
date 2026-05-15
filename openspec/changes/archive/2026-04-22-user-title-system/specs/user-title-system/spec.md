## ADDED Requirements

### Requirement: Title calculation based on check-in count

The system SHALL calculate a user's title based on the number of unique stores checked in (stored in Firestore `user_footprint/<user_id>`):

- 0–4 unique stores: 「無職轉生者」
- 5–14 unique stores: 「肉汁騎士」
- 15–29 unique stores: 「滷鍋守護者」
- 30–59 unique stores: 「魯肉飯勇者」
- 60 or more unique stores: 「魯肉飯大神」

The title SHALL be recalculated after every check-in.

#### Scenario: User checks in and title unchanged

- **WHEN** a user completes a check-in
- **AND** the newly calculated title matches `current_title` in Firestore
- **THEN** the system SHALL NOT trigger an upgrade event

#### Scenario: User checks in and title increases

- **WHEN** a user completes a check-in
- **AND** the newly calculated title differs from `current_title` in Firestore
- **THEN** the system SHALL trigger a title upgrade event

---

### Requirement: Title number assignment

The system SHALL assign a title number to each user encoding both rank and identity.

For 無職轉生者, the title number SHALL be the last 4 characters of the LINE user ID (e.g., `#ab3f`).

For all other titles (肉汁騎士 and above), the title number SHALL be formatted as `{global_counter}-{last_4_of_user_id}` (e.g., `#1-ab3f`), where:
- `global_counter` is atomically incremented via a Firestore transaction on `title_counter/<title>`
- `last_4_of_user_id` provides user identity within the same rank

This format provides both the rarity signal (counter) and user identification (suffix).

Title numbers SHALL NOT change once assigned for a given title. A new title number SHALL be assigned when the user upgrades to a higher title.

#### Scenario: User reaches 肉汁騎士 for the first time

- **WHEN** a user's title upgrades to 「肉汁騎士」
- **THEN** the system SHALL atomically increment `title_counter/肉汁騎士` in Firestore
- **AND** compose the title number as `{count}-{user_id[-4:]}`
- **AND** store the resulting number as `title_number` in `user_footprint/<user_id>`
- **AND** update `current_title` to 「肉汁騎士」

---

### Requirement: Upgrade ceremony message

When a title upgrade event is triggered, the system SHALL send a dedicated upgrade ceremony Flex Message after the check-in confirmation message.

The ceremony Flex Message SHALL use a dark RPG-style design with:
- Header (dark navy `#1A1A2E`): `✦ 稱號解鎖 ✦` label and old title → new title progression
- Body (dark blue `#16213E`): large title emoji, new title in gold, title number, uncle persona congratulatory message

Each title SHALL have a dedicated emoji:
- 肉汁騎士: 🗡️
- 滷鍋守護者: 🛡️
- 魯肉飯勇者: ⚔️
- 魯肉飯大神: 👑

Each title SHALL have multiple pre-written uncle persona upgrade messages, one chosen at random.

#### Scenario: Upgrade ceremony delivered

- **WHEN** a title upgrade event is triggered
- **THEN** the system SHALL send a Flex Message ceremony showing the old title, new title, emoji, and uncle message
- **AND** the Flex Message SHALL be sent as a separate reply after the check-in confirmation text message

---

### Requirement: Title query

The system SHALL handle the keyword「我的稱號」as a query trigger.

The system SHALL reply with a Flex Message (dark brown header, cream body) showing:
- Current title in large gold text with the title number
- 🍚 emoji
- Unique check-in count out of 96
- Uncle certification phrase for the current title
- Progress toward the next title (if not at maximum)

For 魯肉飯大神, no next-title progress SHALL be shown.

Each title has a certification phrase assigned by the uncle:
- 無職轉生者: 「初踏江湖，年輕人終究是年輕人！」
- 肉汁騎士: 「年紀輕輕就有坐騎，前途無量！」
- 滷鍋守護者: 「魯肉飯是你的摯愛，你甘願為它赴湯蹈火」
- 魯肉飯勇者: 「身經百戰，一碗魯肉飯的好壞騙不了你」
- 魯肉飯大神: 「這世界居然有人自稱為大神，大叔甘拜下風🙇」

#### Scenario: User queries their title with check-ins

- **WHEN** a user sends「我的稱號」
- **AND** the user has check-in records
- **THEN** the system SHALL reply with a Flex Message showing title, title number, unique check-in count, certification phrase, and progress to next level

#### Scenario: User queries title with no check-ins

- **WHEN** a user sends「我的稱號」
- **AND** the user has no check-in records
- **THEN** the system SHALL reply with a Flex Message showing the default 無職轉生者 title and certification phrase
