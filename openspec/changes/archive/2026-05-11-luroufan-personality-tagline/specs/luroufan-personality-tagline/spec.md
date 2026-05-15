## ADDED Requirements

### Requirement: Personality tagline mapping

The system SHALL map a user's taste quiz answers to a personality tagline using the following priority rules:

1. If `sauce_taste` is `偏甜` → tagline: 「轉生成南部甜心的我，今天也在滷鍋裡融化人心」
2. If all four dimensions are `都可以` → tagline: 「明明什麼都可以，卻意外成為魯肉飯最強通吃者」
3. Otherwise, match by `fat_ratio` + `skin` + `sauce_consistency`:
   - `偏肥` / `with_skin` / `水` → 「在滷汁迷宮尋求黏嘴邂逅是否搞錯了什麼」
   - `偏肥` / `with_skin` / `稠` → 「因為太思念那鍋濃稠滷汁而觸犯禁忌的我，打開了魯肉飯的真相之門」
   - `偏肥` / `without_skin` / `水` → 「明明只想吃碗魯肉飯，卻不小心踏上滷鼎雙修之路」
   - `偏瘦` / `without_skin` / `水` → 「我也曾經以為魯肉飯一定要肥，直到遇見那碗瘦瘦的你」
   - `偏瘦` / `without_skin` / `稠` → 「明明沒有油花與膠質，卻靠鹹香濃汁成為最強魯肉飯」
4. If no rule matches (e.g., partial 都可以 with no specific combination) → tagline: 「明明什麼都可以，卻意外成為魯肉飯最強通吃者」

#### Scenario: 偏甜 takes priority

- **WHEN** the user's `sauce_taste` answer is `偏甜` regardless of other dimensions
- **THEN** the system SHALL return the 南部甜心 tagline

#### Scenario: All 都可以 returns 通吃者 tagline

- **WHEN** all four quiz dimensions are answered as `都可以`
- **THEN** the system SHALL return the 通吃者 tagline

#### Scenario: Specific combination matched

- **WHEN** the user's answers match one of the five listed fat/skin/sauce combinations and sauce_taste is not 偏甜
- **THEN** the system SHALL return the corresponding tagline

#### Scenario: Unmatched combination falls back to 通吃者

- **WHEN** the user's answers do not match any specific combination (e.g., partial 都可以 with no exact match)
- **THEN** the system SHALL return the 通吃者 tagline
