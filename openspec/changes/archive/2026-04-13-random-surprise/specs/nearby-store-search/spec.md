## ADDED Requirements

### Requirement: Random nearby store search mode

The system SHALL provide a `search_random_nearby_store(lat, lng, store_notes)` function that selects one store randomly from nearby stores using a two-tier radius strategy:
1. Prefer stores within 3 km (primary radius)
2. If none found within 3 km, expand to 5 km (extended radius)
3. If none found within 5 km, return None

This function SHALL operate independently from `search_nearby_stores` and SHALL NOT apply style similarity scoring or threshold filtering.

#### Scenario: Random store selected within primary radius

- **WHEN** `search_random_nearby_store` is called with valid coordinates and at least one store is within 3 km
- **THEN** the function SHALL return one randomly selected store with `store_name` and `distance_km`

#### Scenario: Radius expanded to 5 km when no stores within 3 km

- **WHEN** no store exists within 3 km but at least one store is within 5 km
- **THEN** the function SHALL return one randomly selected store from within 5 km

#### Scenario: No stores within extended radius

- **WHEN** no store exists within 5 km
- **THEN** the function SHALL return None
