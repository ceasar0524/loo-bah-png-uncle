## MODIFIED Requirements

### Requirement: Tie detection

The system SHALL detect when multiple stores are sufficiently close in normalized vote count that no clear winner can be determined, and return all tied stores as candidates instead of forcing a single result.

A tie SHALL be declared when two or more stores have normalized vote counts within a configurable margin (default: 0.15) of the highest normalized vote count. This replaces the previous requirement of strictly equal normalized vote counts.

#### Scenario: Tie returns multiple candidates

- **WHEN** two or more stores have normalized vote counts within tie_margin of the highest normalized vote count
- **THEN** the system SHALL return a result with `is_tie: true` and all tied stores listed in the matches list, ordered by average cosine similarity descending

#### Scenario: Clear majority not a tie

- **WHEN** one store has a normalized vote count that exceeds all others by more than tie_margin
- **THEN** the system SHALL proceed with normal majority vote result and `is_tie: false`

#### Scenario: Tie margin configurable

- **WHEN** the caller specifies a custom tie_margin
- **THEN** the system SHALL apply that margin instead of the default 0.15
