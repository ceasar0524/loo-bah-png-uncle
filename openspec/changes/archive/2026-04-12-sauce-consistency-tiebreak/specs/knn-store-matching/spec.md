## MODIFIED Requirements

### Requirement: Tie detection

The system SHALL detect when multiple stores are sufficiently close in normalized vote count that no clear winner can be determined, and return all tied stores as candidates instead of forcing a single result.

A tie SHALL be declared when two or more stores have normalized vote counts within a configurable margin (default: 0.15) of the highest normalized vote count. This replaces the previous requirement of strictly equal normalized vote counts.

When a tie is detected and Haiku features are available, the system SHALL rank tied stores using a combined score of Haiku feature compatibility and average cosine similarity. The Haiku feature scoring SHALL use the same rules as the override mechanism (topping matches, distinctive bowl features). Stores with higher Haiku scores SHALL be ranked above stores with no Haiku score. When Haiku scores are equal, stores SHALL be ranked by average cosine similarity descending.

After Haiku ranking, if `DINO_TIEBREAK_ENABLED` is `"true"` and the top two candidates have different `sauce_consistency` labels in `store_notes.json`, the system SHALL apply the sauce consistency tiebreak as a final ranking step. See `sauce-consistency-tiebreak` spec for full conditions.

#### Scenario: Tie returns multiple candidates

- **WHEN** two or more stores have normalized vote counts within tie_margin of the highest normalized vote count
- **THEN** the system SHALL return a result with `is_tie: true` and all tied stores listed in the matches list, ordered by (Haiku feature score descending, average cosine similarity descending), with sauce consistency tiebreak applied last if conditions are met

#### Scenario: Tie ranking uses Haiku features when available

- **WHEN** a tie is detected and haiku_features are provided
- **THEN** tied stores with detected toppings or bowl features matching their store_notes SHALL be ranked above stores with no Haiku feature match

#### Scenario: Sauce consistency tiebreak applied after Haiku ranking

- **WHEN** a tie remains after Haiku ranking and top two candidates have different sauce_consistency labels and DINO_TIEBREAK_ENABLED is true
- **THEN** the candidate whose sauce_consistency matches the DINOv2 prediction SHALL be ranked first

#### Scenario: Clear majority not a tie

- **WHEN** one store has a normalized vote count that exceeds all others by more than tie_margin
- **THEN** the system SHALL proceed with normal majority vote result and `is_tie: false`

#### Scenario: Tie margin configurable

- **WHEN** the caller specifies a custom tie_margin
- **THEN** the system SHALL apply that margin instead of the default 0.15
