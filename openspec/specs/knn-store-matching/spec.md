# knn-store-matching Specification

## Purpose

TBD - created by archiving change 'store-matching'. Update Purpose after archive.

## Requirements

### Requirement: KNN store matching

The system SHALL load the embedding index and find the K most similar photo vectors to the query embedding using cosine similarity, then determine the matching store by photo-count-normalized vote among the top-K results.

The vote for each store SHALL be normalized by dividing the raw vote count by that store's total photo count, ensuring stores with fewer photos are not disadvantaged against stores with larger photo libraries.

The default value of K SHALL be 5. K SHALL be configurable by the caller.

#### Scenario: Store identified by normalized vote

- **WHEN** a query embedding is provided and K=5
- **THEN** the system SHALL find the 5 most similar vectors in the index, compute each store's normalized vote (raw vote count / photo_count), and return the store with the highest normalized vote

#### Scenario: Normalized vote corrects for unequal photo counts

- **WHEN** store A has 15 photos and store B has 3 photos and both receive 2 votes in top-K
- **THEN** store B's normalized vote (2/3) SHALL be higher than store A's (2/15), and store B SHALL win

#### Scenario: Similarity score computed as average

- **WHEN** a winning store is determined by majority vote
- **THEN** the similarity score SHALL be the average cosine similarity of the winning store's vectors among the top-K results

#### Scenario: Results ordered by similarity descending

- **WHEN** multiple stores meet the similarity threshold
- **THEN** the result list SHALL be ordered by similarity score descending

---
### Requirement: Similarity threshold filtering

The system SHALL filter out stores whose computed similarity score falls below a configurable threshold (default: 0.5). An empty list SHALL be returned when no store meets the threshold.

#### Scenario: Low similarity result excluded

- **WHEN** the winning store's similarity score is below the threshold
- **THEN** the system SHALL return an empty list

#### Scenario: Threshold configurable

- **WHEN** the caller specifies a custom threshold
- **THEN** the system SHALL apply that threshold instead of the default

---
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

---
### Requirement: Similarity confidence level

The system SHALL classify the match similarity into confidence levels to allow the uncle-persona to vary its language accordingly.

- **high**: similarity >= 0.8
- **medium**: 0.5 <= similarity < 0.8
- **low / no match**: similarity < 0.5 or empty matches

#### Scenario: High confidence match

- **WHEN** the winning store's similarity score is >= 0.8
- **THEN** the result SHALL include `confidence_level: "high"`

#### Scenario: Medium confidence match

- **WHEN** the winning store's similarity score is >= 0.5 and < 0.8
- **THEN** the result SHALL include `confidence_level: "medium"`

---
### Requirement: Haiku feature override for high-confidence distinctive features

After the CLIP KNN result is computed, the system SHALL apply a Haiku feature override when the classifier has detected a high-confidence distinctive visual feature that uniquely identifies a store.

The override SHALL consult `data/store_notes.json` for each store's `bowl` entry and `known_toppings`. The override scoring SHALL be:

- Bowl color match on a store marked `distinctive: true`: +0.5
- Bowl shape match on a store marked `distinctive: true`: +0.2
- Bowl texture match on a store marked `distinctive: true`: +0.3
- Cilantro (`cilantro`) detected and present in a store's `known_toppings`: +0.8
- Other topping detected and present in a store's `known_toppings`: +0.3

The override SHALL only fire when a single store reaches or exceeds the override threshold (default: 0.75) with no tie. If multiple stores reach the threshold simultaneously, the override SHALL be suppressed and the CLIP result SHALL be used.

When the override fires, the matched store SHALL be returned with `confidence_level: "high"` regardless of the underlying CLIP similarity score.

When the override does not fire, the CLIP KNN result SHALL be returned unchanged.

#### Scenario: Distinctive bowl colour triggers override

- **WHEN** the classifier detects `bowl_color: "bright_green"` and store 晴光小吃 has `bowl.color: "bright_green"` with `distinctive: true`
- **THEN** the system SHALL override the CLIP result and return 晴光小吃 with `confidence_level: "high"`

#### Scenario: Cilantro triggers override for 阿興

- **WHEN** the classifier detects `cilantro` in toppings and 阿興魯肉飯 has `cilantro` in `known_toppings`
- **THEN** the system SHALL override the CLIP result and return 阿興魯肉飯 with `confidence_level: "high"`

#### Scenario: Override suppressed when multiple stores qualify

- **WHEN** detected features match more than one store above the override threshold
- **THEN** the system SHALL suppress the override and return the CLIP KNN result unchanged

#### Scenario: No distinctive features falls back to CLIP

- **WHEN** no detected feature scores any store at or above the override threshold
- **THEN** the system SHALL return the CLIP KNN result unchanged

---
### Requirement: Result conforms to store-matching-schema

The system SHALL return results conforming to the store-matching-schema defined in data-schema, including store_name, similarity, and photo_count.

#### Scenario: Result includes photo_count

- **WHEN** a match result is returned
- **THEN** each entry SHALL include the photo_count from the index for that store
