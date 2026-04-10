# nearby-store-search Specification

## ADDED Requirements

### Requirement: Search nearby stores by style similarity

The system SHALL accept a matched store name and a user location (latitude, longitude), compute visual_profile similarity between the matched store and all other stores, filter stores within a configurable radius (default: 3 km), and return stores ranked by profile similarity score descending.

Visual profile similarity is computed by comparing three `visual_profile` fields: `fat_ratio`, `skin`, and `sauce_color`. `rice_quality` is excluded due to low discriminative power (most stores share the same value). Each matching field contributes equally to the similarity score (score = number of matching fields / 3).

Stores with a similarity score below 0.5 SHALL be excluded from results, regardless of distance.

The distance between user location and store location SHALL be computed using the Haversine formula.

Stores without a location entry in store_notes.json SHALL be excluded from results.

The system SHALL return at most 3 nearby store candidates. The persona layer SHALL present at most 2 stores to the user, ordered by distance ascending (nearest first).

#### Scenario: Nearby stores found within radius

- **WHEN** a matched store name and user location are provided and at least one store is within the radius with profile similarity above threshold
- **THEN** the system SHALL return up to 3 stores ordered by profile similarity score descending, each with store_name, similarity_score, and distance_km

#### Scenario: No stores within radius

- **WHEN** no store is within the configured radius
- **THEN** the system SHALL return an empty results list with `any_in_radius=False`

#### Scenario: Stores within radius but none pass similarity threshold

- **WHEN** at least one store is within the configured radius but none have similarity score ≥ 0.5
- **THEN** the system SHALL return an empty results list with `any_in_radius=True`

#### Scenario: Queried store excluded from results

- **WHEN** the matched store from the original recognition is within the radius
- **THEN** that store SHALL be excluded from the nearby recommendation results

### Requirement: Store location data

Each store in store_notes.json SHALL have a `location` field containing `lat` (latitude) and `lng` (longitude) in decimal degrees.

#### Scenario: Store with location data

- **WHEN** a store has a valid `location.lat` and `location.lng` entry
- **THEN** the system SHALL include that store in the distance computation

#### Scenario: Store without location data

- **WHEN** a store has no `location` entry
- **THEN** the system SHALL skip that store in nearby search
