# title-skill-meat-shield Specification

## Purpose

TBD - created by archiving change 'title-unlock-skills'. Update Purpose after archive.

## Requirements

### Requirement: Meat Shield activation

The system SHALL provide a skill called「肉盾」unlocked at Lv.1 (「肉汁騎士」or above).

When a user with Lv.1+ title sends the text「肉盾」, the system SHALL reply asking which store to evaluate, prompting the user to type a store name.

When the user types a store name, the system SHALL perform fuzzy matching against all stores in `_store_notes` and `_hidden_gems` and return the best match.

#### Scenario: User sends 肉盾 at Lv.1+

- **WHEN** a user with title 「肉汁騎士」or above sends the text「肉盾」
- **THEN** the system SHALL reply with「🛡️ 肉盾發動！你想讓大叔先幫你擋哪一家？輸入店名」

#### Scenario: User sends 肉盾 below Lv.1

- **WHEN** a user with title「無職轉生者」sends the text「肉盾」
- **THEN** the system SHALL NOT trigger the meat shield skill
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
### Requirement: Meat Shield evaluation with taste profile

When the user submits a store name and the user has a saved taste preference, the system SHALL compare the store's taste attributes against the user's preference and return a verdict.

The verdict SHALL be one of:
- 🟢 **適合衝** — store attributes closely match user's preference
- 🟡 **可以試** — partial match, some attributes differ
- 🔴 **小心踩雷** — store attributes significantly differ from user's preference

The reply SHALL include the store's taste characteristics and a brief explanation for the verdict.

#### Scenario: User with taste profile queries a matching store

- **WHEN** a user has a saved taste preference
- **AND** the user queries a store whose attributes closely match their preference
- **THEN** the system SHALL return 🟢 適合衝 with explanation

#### Scenario: User with taste profile queries a mismatching store

- **WHEN** a user has a saved taste preference
- **AND** the user queries a store whose attributes significantly differ from their preference
- **THEN** the system SHALL return 🔴 小心踩雷 with explanation


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
### Requirement: Meat Shield evaluation without taste profile

When the user has no saved taste preference, the system SHALL return store information only without a verdict, and SHALL prompt the user to fill in their taste preference for personalized evaluation.

#### Scenario: User without taste profile queries a store

- **WHEN** a user has no saved taste preference
- **AND** the user queries a store via 肉盾
- **THEN** the system SHALL return store taste characteristics without a 🟢🟡🔴 verdict
- **AND** the system SHALL suggest the user fill in their taste preference


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
### Requirement: Fuzzy store name matching

The system SHALL perform fuzzy matching on the user's input against all store names. If no match is found, the system SHALL reply asking the user to try another name.

If multiple stores match the input, the system SHALL list all matching stores and prompt the user to select one before proceeding with evaluation.

#### Scenario: Store name found via fuzzy match — single result

- **WHEN** the user inputs a partial store name
- **AND** exactly one matching store exists in the database
- **THEN** the system SHALL proceed with the matched store's data

#### Scenario: Store name found via fuzzy match — multiple results

- **WHEN** the user inputs a partial store name
- **AND** multiple matching stores exist in the database
- **THEN** the system SHALL list all matching stores and ask the user to select one

#### Scenario: No matching store found

- **WHEN** the user inputs a store name that does not match any store
- **THEN** the system SHALL reply indicating no match was found and ask the user to try again

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