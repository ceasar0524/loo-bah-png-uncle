# title-skill-decree Specification

## Purpose

TBD - created by archiving change 'title-unlock-skills'. Update Purpose after archive.

## Requirements

### Requirement: Decree wall accessible to all users

The system SHALL allow any user to view the「大神推薦牆」(Decree Wall) by selecting it from the「巷子口」store list menu.

The Decree Wall SHALL display all of today's recommendations posted by「魯肉飯大神」users. Multiple decrees SHALL all be shown. Each entry SHALL display the poster's title display ID (e.g.,「魯肉飯大神#1-f3f9」) in the format:

```
📜 今日滷令

魯肉飯大神#1-f3f9 推薦：
{store_name}

理由：
{reason}


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

魯肉飯大神#2-a2b8 推薦：
{store_name}

理由：
{reason}
```

#### Scenario: Any user views the Decree Wall

- **WHEN** any user selects the Decree Wall option from the 巷子口 menu
- **THEN** the system SHALL display all of today's 大神 recommendations
- **AND** each entry SHALL show the poster's title display ID
- **AND** if no recommendations exist for today, the system SHALL display a message indicating no decree has been issued today

---
### Requirement: Decree posting for 魯肉飯大神 users

The system SHALL allow users with title「魯肉飯大神」(Lv.4) to post a daily decree by sending the text「號令」.

Each 大神 user SHALL be limited to one decree per calendar day (Taiwan time, UTC+8).

When a 大神 user sends「號令」, the system SHALL guide them through:
1. Entering a store name to recommend (free text input, not limited to stores in the system database)
2. Entering the reason for recommending the store

The store name SHALL be limited to 20 characters. The reason SHALL be limited to 50 characters. If either input exceeds the limit, the system SHALL reject and ask the user to re-enter.

The system SHALL apply a keyword blocklist to both store name and reason. If blocked content is detected, the system SHALL reply「大叔審核不通過，請重新輸入」and prompt again.

#### Scenario: 大神 user sends 號令 with no decree today

- **WHEN** a user with title「魯肉飯大神」sends the text「號令」
- **AND** the user has not posted a decree today
- **THEN** the system SHALL prompt the user to enter the store name they wish to recommend

#### Scenario: 大神 user sends 號令 after already posting today

- **WHEN** a user with title「魯肉飯大神」sends the text「號令」
- **AND** the user has already posted a decree today
- **THEN** the system SHALL reply indicating today's decree has already been issued and show the posted content

#### Scenario: 大神 user submits store name exceeding character limit

- **WHEN** a 大神 user enters a store name longer than 20 characters
- **THEN** the system SHALL reject the input and ask the user to re-enter within 20 characters

#### Scenario: 大神 user submits reason exceeding character limit

- **WHEN** a 大神 user enters a reason longer than 50 characters
- **THEN** the system SHALL reject the input and ask the user to re-enter within 50 characters

#### Scenario: 大神 user submits content with blocked keywords

- **WHEN** a 大神 user's store name or reason contains a blocked keyword
- **THEN** the system SHALL reply「大叔審核不通過，請重新輸入」and prompt again

#### Scenario: Below Lv.4 user sends 號令

- **WHEN** a user with title below「魯肉飯大神」sends the text「號令」
- **THEN** the system SHALL NOT trigger the decree posting flow
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
### Requirement: Decree data persistence

Each posted decree SHALL be stored in Firestore under `decrees/{date}/{user_id}` with fields: `store_name`, `reason`, `posted_at`, `user_id`.

#### Scenario: Decree is stored after posting

- **WHEN** a 大神 user completes the decree posting flow
- **THEN** the system SHALL write the decree to Firestore
- **AND** the decree SHALL be retrievable by all users via the Decree Wall

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