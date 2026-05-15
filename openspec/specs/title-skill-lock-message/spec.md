# title-skill-lock-message Specification

## Purpose

TBD - created by archiving change 'title-unlock-skills'. Update Purpose after archive.

## Requirements

### Requirement: Skill lock message for insufficient title

When a user triggers a skill keyword but does not meet the required title level, the system SHALL reply with a lock message instead of executing the skill.

The lock message format SHALL be:

```
🔒 技能尚未解鎖

這招目前還被封印中。
你現在是【{current_title}】，還差 {N} 家才能解鎖【{skill_name}】。

繼續攻略魯肉飯，累積足跡吧 🍚
```

Where:
- `{current_title}` is the user's current title (e.g.,「無職轉生者」「肉汁騎士」)
- `{N}` is the number of additional unique check-ins required to reach the skill's required title level, calculated as `required_threshold - current_unique_count`
- `{skill_name}` is the name of the triggered skill (e.g.,「肉盾」「絕對滷域」「魯拉（ルラ）」「滷界敕令」)

The required thresholds per skill are:
- 肉盾 → requires「肉汁騎士」(5 unique stores)
- 絕對滷域 → requires「滷鍋守護者」(15 unique stores)
- 魯拉（ルラ） → requires「魯肉飯勇者」(30 unique stores)
- 滷界敕令 → requires「魯肉飯大神」(60 unique stores)

#### Scenario: User below required level triggers a skill

- **WHEN** a user with insufficient title level triggers a skill keyword
- **THEN** the system SHALL NOT execute the skill
- **AND** the system SHALL reply with the lock message showing the user's current title and number of stores needed to unlock the skill

#### Scenario: Lock message shows correct remaining count

- **WHEN** a user with 3 unique check-ins triggers「肉盾」(requires 5)
- **THEN** the lock message SHALL state「還差 2 家才能解鎖【肉盾】」

#### Scenario: Lock message shows correct remaining count for distant skill

- **WHEN** a user with 0 unique check-ins triggers「魯拉」(requires 30)
- **THEN** the lock message SHALL state「還差 30 家才能解鎖【魯拉（ルラ）】」

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