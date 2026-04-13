## ADDED Requirements

### Requirement: Random nearby store recommendation

The system SHALL accept a user location (latitude, longitude) and return one randomly selected store from within a configurable radius (default: 3 km).

If no store exists within the radius, the system SHALL expand to all stores and return one randomly selected store.

The selected store SHALL include `store_name`, `distance_km`, and a brief style description derived from `store_notes`.

#### Scenario: Stores found within radius

- **WHEN** a user location is provided and at least one store exists within 3 km
- **THEN** the system SHALL randomly select one store from within the radius and return it with `store_name` and `distance_km`

#### Scenario: No stores within radius

- **WHEN** no store exists within the 3 km radius
- **THEN** the system SHALL randomly select one store from all collected stores and return it with `store_name` and `distance_km`

#### Scenario: Random selection is uniform

- **WHEN** multiple stores are available within the radius
- **THEN** each store SHALL have an equal probability of being selected

### Requirement: Random recommendation response format

The uncle persona SHALL generate a response for the random nearby recommendation using `generate_random`, referencing the store's style attributes from `store_notes` (fat_ratio, skin, sauce_color, sauce_taste).

#### Scenario: Store has style data

- **WHEN** the randomly selected store has `visual_profile` entries in `store_notes`
- **THEN** the response SHALL include a brief style description (e.g., 偏肥、帶皮、醬汁深色)

#### Scenario: Store has no style data

- **WHEN** the randomly selected store has no `visual_profile` in `store_notes`
- **THEN** the response SHALL omit style details and return a location-only recommendation
