# store-matching-schema Specification

## Purpose

TBD - created by archiving change 'data-schema'. Update Purpose after archive.

## Requirements

### Requirement: Store matching result schema

The store matching module SHALL return a response conforming to the following structure:

```
{
  "is_tie": bool,              # true when top-K votes are evenly split
  "matches": [
    {
      "store_name": str,           # store directory name / display name
      "similarity": float,         # cosine similarity, 0.0–1.0
      "confidence_level": str,     # "high" (>=0.8) | "medium" (0.5–0.8)
      "photo_count": int           # number of photos in this store's dataset
    },
    ...
  ]
}
```

`matches` SHALL be ordered by descending similarity. `matches` SHALL be empty when no store meets the similarity threshold or when `is_tie` is true.

#### Scenario: Multiple matches returned

- **WHEN** multiple stores meet the similarity threshold
- **THEN** matches SHALL be a list ordered by similarity descending, each entry containing store_name, similarity, confidence_level, and photo_count

#### Scenario: No matches returned

- **WHEN** no store meets the similarity threshold
- **THEN** matches SHALL be an empty list and is_tie SHALL be false

#### Scenario: Tie returned

- **WHEN** top-K votes are evenly split with no majority
- **THEN** is_tie SHALL be true and matches SHALL be an empty list

#### Scenario: photo_count included

- **WHEN** a match result is returned
- **THEN** each entry SHALL include the photo_count of that store's dataset
