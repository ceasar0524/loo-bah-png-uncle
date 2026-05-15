# user-title-system Specification

## Purpose

TBD - created by archiving change 'user-title-system'. Update Purpose after archive.

## Requirements

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


<!-- @trace
source: user-title-system
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

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


<!-- @trace
source: user-title-system
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

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


<!-- @trace
source: user-title-system
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

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

<!-- @trace
source: user-title-system
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Upgrade Flex Message includes skill unlock announcement

The upgrade Flex Message displayed upon title advancement SHALL include a skill unlock section below the upgrade message body.

The skill unlock section SHALL display:
- The skill name (e.g.,「肉盾」「絕對滷域」「魯拉（ルラ）」「滷界敕令」)
- The unlock announcement text defined per title level

Unlock announcement text per title:

**肉汁騎士 (Lv.1)**:
> 技能解鎖：肉盾
>
> 大叔的第一個禮物。
> 輸入「肉盾」，告訴大叔你想去吃哪家，
> 大叔會依照你的口味偏好，幫你先擋雷。

**滷鍋守護者 (Lv.2)**:
> 技能解鎖：絕對滷域
>
> 你打卡過的魯肉飯店，
> 已經開始形成專屬守護領域。
>
> 從現在開始，可以用地圖查看自己的魯肉飯版圖。

**魯肉飯勇者 (Lv.3)**:
> 技能解鎖：魯拉
>
> 吃過的店，
> 都將成為你的傳送據點。
>
> 輸入「魯拉」，
> 選擇曾經攻略過的店，
> 即可一鍵開啟 Google Maps 導航，
> 回到那碗熟悉的魯肉飯。

**魯肉飯大神 (Lv.4)**:
> 技能解鎖：滷界敕令
>
> 你已不只是吃飯的人，
> 而是能向眾勇者發布推薦的大神。
>
> 輸入「號令」，
> 選擇你認可的魯肉飯店，
> 留下推薦理由，
> 讓它登上大神推薦牆。

#### Scenario: User upgrades to 肉汁騎士

- **WHEN** a user's title advances to「肉汁騎士」
- **THEN** the upgrade Flex Message SHALL include the 肉盾 skill unlock announcement

#### Scenario: User upgrades to 滷鍋守護者

- **WHEN** a user's title advances to「滷鍋守護者」
- **THEN** the upgrade Flex Message SHALL include the 絕對滷域 skill unlock announcement

#### Scenario: User upgrades to 魯肉飯勇者

- **WHEN** a user's title advances to「魯肉飯勇者」
- **THEN** the upgrade Flex Message SHALL include the 魯拉 skill unlock announcement

#### Scenario: User upgrades to 魯肉飯大神

- **WHEN** a user's title advances to「魯肉飯大神」
- **THEN** the upgrade Flex Message SHALL include the 滷界敕令 skill unlock announcement

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