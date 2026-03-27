## ADDED Requirements

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

### Requirement: Similarity threshold filtering

The system SHALL filter out stores whose computed similarity score falls below a configurable threshold (default: 0.5). An empty list SHALL be returned when no store meets the threshold.

#### Scenario: Low similarity result excluded

- **WHEN** the winning store's similarity score is below the threshold
- **THEN** the system SHALL return an empty list

#### Scenario: Threshold configurable

- **WHEN** the caller specifies a custom threshold
- **THEN** the system SHALL apply that threshold instead of the default

### Requirement: Tie detection

The system SHALL detect when multiple stores share the highest normalized vote count with no clear winner, and return all tied stores as candidates instead of forcing a single result.

A tie SHALL be declared when two or more stores share the highest normalized vote count after photo-count normalization.

#### Scenario: Tie returns multiple candidates

- **WHEN** two or more stores share the highest normalized vote count
- **THEN** the system SHALL return a result with `is_tie: true` and all tied stores listed in the matches list, ordered by average cosine similarity descending

#### Scenario: Clear majority not a tie

- **WHEN** one store has strictly more normalized votes than all others
- **THEN** the system SHALL proceed with normal majority vote result and `is_tie: false`

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

### Requirement: Result conforms to store-matching-schema

The system SHALL return results conforming to the store-matching-schema defined in data-schema, including store_name, similarity, and photo_count.

#### Scenario: Result includes photo_count

- **WHEN** a match result is returned
- **THEN** each entry SHALL include the photo_count from the index for that store
